"""Thin wrapper over the Anthropic SDK for the orchestrator and workers.

Treats every model call as an unreliable, metered dependency: JSON-schema structured output,
validation at the boundary, refusal and truncation handled as typed errors, and every call's
token usage priced and written to the store so a run can enforce a dollar budget.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic

from .store import Store

PLANNER_MODEL = os.environ.get("LPLAB_PLANNER_MODEL", "claude-opus-5-5")
WORKER_MODEL = os.environ.get("LPLAB_WORKER_MODEL", "claude-haiku-5-5")

# USD per million tokens: (input, output, cache read). Haiku 5.5 rate is for prompts <= 100K.
PRICES: dict[str, tuple[float, float, float]] = {
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10),
}
_FALLBACK_BETA = "server-side-fallback-2026-07-01"
_FALLBACK_MODELS = frozenset({"claude-opus-5-5", "claude-sonnet-5-5"})


class LLMError(RuntimeError):
    """A model call that returned nothing usable (refusal, truncation, invalid JSON)."""


class MessagesClient(Protocol):
    """The slice of ``anthropic.Anthropic`` we use; tests pass a fake."""

    @property
    def beta(self) -> Any: ...


def price(model: str, usage: Any) -> float:
    pin, pout, pcache = PRICES.get(model, PRICES["claude-opus-5-5"])
    inp = getattr(usage, "input_tokens", 0) or 0
    out = getattr(usage, "output_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    return (inp * pin + out * pout + cache_read * pcache + cache_write * pin * 1.25) / 1e6


@dataclass
class LLM:
    store: Store
    client: MessagesClient | None = None
    calls: int = field(default=0, init=False)

    def _client(self) -> MessagesClient:
        if self.client is None:
            self.client = anthropic.Anthropic(max_retries=3, timeout=600.0)
        return self.client

    def json_call(
        self,
        *,
        role: str,
        model: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        effort: str = "high",
        max_tokens: int = 16000,
    ) -> dict[str, Any]:
        """One structured-output call. Returns the parsed JSON object or raises LLMError."""
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            # stable system prompt first and cached; volatile lab state goes in the user turn
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": user}],
            "output_config": {
                "effort": effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        }
        if model in _FALLBACK_MODELS:
            kwargs["betas"] = [_FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        try:
            resp = self._client().beta.messages.create(**kwargs)
        except anthropic.AuthenticationError as e:
            raise LLMError("Anthropic credentials missing or invalid (ANTHROPIC_API_KEY)") from e
        except anthropic.BadRequestError as e:
            raise LLMError(f"bad request for {role}: {e.message}") from e
        except anthropic.RateLimitError as e:
            raise LLMError(f"rate limited after retries for {role}") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"API error {e.status_code} for {role}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError(f"network error for {role}") from e

        self.calls += 1
        served = getattr(resp, "model", model) or model
        usage = resp.usage
        self.store.record_llm_call(
            role,
            served,
            getattr(usage, "input_tokens", 0) or 0,
            getattr(usage, "output_tokens", 0) or 0,
            getattr(usage, "cache_read_input_tokens", 0) or 0,
            price(served, usage),
        )
        if resp.stop_reason == "refusal":
            raise LLMError(f"{role} call refused")
        if resp.stop_reason == "max_tokens":
            raise LLMError(f"{role} call hit max_tokens; output truncated")
        text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), None)
        if text is None:
            raise LLMError(f"{role} call returned no text block")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"{role} returned invalid JSON: {e}") from e
        if not isinstance(data, dict):
            raise LLMError(f"{role} returned {type(data).__name__}, expected object")
        return data

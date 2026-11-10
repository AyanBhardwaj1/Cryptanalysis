"""Fake Anthropic client for tests: no network, no API key.

``FakeClient`` mimics ``anthropic.Anthropic(...).beta.messages.create`` and records each call's
kwargs in ``calls`` so tests can assert on what was sent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any


def make_response(
    text: str,
    *,
    model: str,
    stop_reason: str = "end_turn",
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_read: int = 0,
    cache_write: int = 0,
) -> SimpleNamespace:
    """Shape of an ``anthropic`` beta messages response, as far as lplab reads it."""
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_write,
        ),
        stop_reason=stop_reason,
        model=model,
    )


class _FakeMessages:
    def __init__(self, owner: FakeClient) -> None:
        self._owner = owner

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self._owner.calls.append(kwargs)
        if self._owner.queue:
            text, stop = self._owner.queue.pop(0)
        else:
            text, stop = "{}", "end_turn"
        return make_response(text, model=kwargs["model"], stop_reason=stop)


class _FakeBeta:
    def __init__(self, owner: FakeClient) -> None:
        self.messages = _FakeMessages(owner)


@dataclass
class FakeClient:
    """Stands in for ``anthropic.Anthropic``. Replies are popped from ``queue`` in order.

    Each call's kwargs are appended to ``calls`` so tests can assert on what was sent.
    """

    queue: list[tuple[str, str]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.beta = _FakeBeta(self)

    def reply(self, text: str, stop_reason: str = "end_turn") -> None:
        self.queue.append((text, stop_reason))

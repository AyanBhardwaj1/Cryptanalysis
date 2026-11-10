"""The LLM wrapper, exercised through a fake Anthropic client (no network, no API key)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fakes import FakeClient

from lplab import llm as L
from lplab.store import Store

OPUS = "claude-opus-5-5"
HAIKU = "claude-haiku-5-5"
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}


def _call(client: L.LLM, model: str = HAIKU) -> dict:
    return client.json_call(role="test", model=model, system="sys", user="hi", schema=SCHEMA)


def test_json_call_returns_the_parsed_object(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply(json.dumps({"ok": True, "n": 3}))
    assert _call(llm) == {"ok": True, "n": 3}


def test_json_call_records_its_cost_in_the_store(
    llm: L.LLM, fake_client: FakeClient, store: Store
) -> None:
    fake_client.reply("{}")
    _call(llm, HAIKU)
    # 100 input tokens at $0.10/M plus 50 output tokens at $0.50/M
    assert store.total_cost() == pytest.approx((100 * 0.10 + 50 * 0.50) / 1e6)


def test_price_of_one_million_opus_input_tokens_is_four_dollars() -> None:
    usage = SimpleNamespace(
        input_tokens=1_000_000,
        output_tokens=0,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )
    assert L.price(OPUS, usage) == pytest.approx(4.0)


def test_refusal_raises_llm_error(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply("{}", stop_reason="refusal")
    with pytest.raises(L.LLMError, match="refused"):
        _call(llm)


def test_max_tokens_stop_raises_llm_error(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply('{"ok": tr', stop_reason="max_tokens")
    with pytest.raises(L.LLMError, match="max_tokens"):
        _call(llm)


def test_invalid_json_raises_llm_error(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply("this is not json")
    with pytest.raises(L.LLMError, match="invalid JSON"):
        _call(llm)


def test_json_array_instead_of_object_raises_llm_error(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply("[1, 2, 3]")
    with pytest.raises(L.LLMError, match="expected object"):
        _call(llm)


def test_opus_call_requests_server_fallbacks_and_beta(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply("{}")
    _call(llm, OPUS)
    sent = fake_client.calls[-1]
    assert sent["fallbacks"] == "default"
    assert sent["betas"] == [L._FALLBACK_BETA]


def test_haiku_call_omits_fallbacks_and_betas(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply("{}")
    _call(llm, HAIKU)
    sent = fake_client.calls[-1]
    assert "fallbacks" not in sent
    assert "betas" not in sent


def test_system_prompt_is_sent_as_a_cached_block(llm: L.LLM, fake_client: FakeClient) -> None:
    fake_client.reply("{}")
    _call(llm)
    system = fake_client.calls[-1]["system"]
    assert system == [{"type": "text", "text": "sys", "cache_control": {"type": "ephemeral"}}]


def test_json_call_requests_structured_output_with_the_schema(
    llm: L.LLM, fake_client: FakeClient
) -> None:
    fake_client.reply("{}")
    _call(llm)
    fmt = fake_client.calls[-1]["output_config"]["format"]
    assert fmt == {"type": "json_schema", "schema": SCHEMA}

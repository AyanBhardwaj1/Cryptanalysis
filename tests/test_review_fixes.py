"""Regression tests for the independent review's findings."""

from __future__ import annotations

import numpy as np
import pytest
from fakes import FakeClient
from pydantic import ValidationError

from lplab import ciphers as C
from lplab import corpus
from lplab import hypotheses as H
from lplab.gematria import latin_to_indices
from lplab.llm import LLM, LLMError, price
from lplab.planner import KeywordTask
from lplab.store import Store, _abridge
from lplab.workers import KeywordWorker, run_keyword_tasks


def test_keyword_tasks_in_threads_record_spend_without_crashing(store: Store) -> None:
    # regression: worker threads wrote to a sqlite connection owned by the main thread
    client = FakeClient()
    for _ in range(3):
        client.reply('{"keys": ["DIVINITY", "PRIMES"]}')
    worker = KeywordWorker(LLM(store, client=client))
    tasks = [KeywordTask(theme=f"theme {i}", page="p54-55") for i in range(3)]

    hyps, errors = run_keyword_tasks(worker, tasks)

    assert errors == []
    assert len(hyps) == 3
    assert store.total_cost() > 0


def test_running_key_offsets_are_capped() -> None:
    with pytest.raises(ValidationError):
        H.parse({"family": "running_key", "page": "p54-55", "source": "p40-53",
                 "source_kind": "ciphertext", "offset_max": 5000})  # fmt: skip


def test_expensive_combination_is_rejected_at_validation() -> None:
    # regression: running_key x affine "all" needed ~3 GB in one hypothesis
    with pytest.raises(ValidationError, match="too expensive"):
        H.parse({"family": "running_key", "page": "p54-55", "source": "p40-53",
                 "source_kind": "ciphertext", "affine_mode": "all"})  # fmt: skip
    with pytest.raises(ValidationError, match="too expensive"):
        H.parse({"family": "skip_rule", "page": "p40-53", "key_source": "running",
                 "source": "p8-14", "offset_max": 400, "affine_mode": "shifts",
                 "interrupt_mode": "all"})  # fmt: skip


def test_every_curriculum_hypothesis_fits_the_work_budget() -> None:
    from itertools import islice

    from lplab.planner import curriculum

    for h in islice(curriculum(("p54-55",)), 400):
        assert h.work() <= H.MAX_WORK


def test_llm_refuses_to_call_once_budget_is_spent(store: Store) -> None:
    store.record_llm_call("planner", "claude-opus-5-5", 0, 0, 0, 5.0)
    client = FakeClient()
    llm = LLM(store, client=client, budget_usd=5.0)

    with pytest.raises(LLMError, match="budget"):
        llm.json_call(role="planner", model="claude-opus-5-5", system="s", user="u",
                      schema={"type": "object"})  # fmt: skip
    assert client.calls == []


def test_pricing_matches_served_model_ids_with_suffixes() -> None:
    from types import SimpleNamespace

    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=0)
    assert price("claude-haiku-5-5-20261001", usage) == pytest.approx(0.10)
    assert price("unknown-model", usage) == pytest.approx(4.0)  # conservative default


def test_recent_params_abridge_long_key_lists() -> None:
    out = _abridge({"keys": [f"K{i}" for i in range(50)], "page": "p0-2"})
    assert len(out["keys"]) == 6 and out["keys"][-1] == "... +45 more"
    assert out["page"] == "p0-2"


def test_autokey_with_affine_feeds_back_the_true_plaintext() -> None:
    # regression: the kernel fed back the pre-affine value, so non-identity affines decrypted
    # a different cipher than the detail label said
    pt = corpus.load_solution("0_koan_1").runes
    primer = latin_to_indices("DIVINITY")
    aff = C.Affine(1, 5)
    full_key = np.concatenate([primer, pt[: pt.size - primer.size]])
    ct = C.encrypt_stream(pt, full_key, affine=aff)

    assert np.array_equal(C.autokey(ct, primer, affine=aff), pt)

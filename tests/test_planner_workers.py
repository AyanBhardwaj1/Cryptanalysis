"""Planners and Haiku workers: plan parsing, dedup against the store, and output validation."""

from __future__ import annotations

import json

import pytest
from fakes import FakeClient

from lplab import corpus, scoring
from lplab import hypotheses as H
from lplab.hypotheses import Candidate
from lplab.llm import LLM
from lplab.planner import (
    MAX_KEYWORD_TASKS,
    ClaudePlanner,
    HeuristicPlanner,
    KeywordTask,
    parse_plan,
)
from lplab.store import Store
from lplab.workers import JudgeWorker, KeywordWorker


def _affine_json(page: str = "p54-55") -> str:
    return json.dumps({"family": "affine", "page": page})


def test_parse_plan_keeps_valid_hypotheses_and_rejects_invalid_ones() -> None:
    data = {
        "assessment": "try affines",
        "hypotheses": [
            {"hypothesis_json": _affine_json()},
            {"hypothesis_json": json.dumps({"family": "rot13", "page": "p54-55"})},
        ],
        "keyword_tasks": [],
    }

    plan = parse_plan(data, batch=5)

    assert len(plan.hypotheses) == 1
    assert isinstance(plan.hypotheses[0], H.AffineH)
    assert len(plan.rejected) == 1
    assert "rot13" in plan.rejected[0]


def test_parse_plan_caps_keyword_tasks_at_max_keyword_tasks() -> None:
    task = {"theme": "primes", "page": "p54-55", "family": "vigenere_key", "count": 10}
    data = {"assessment": "", "hypotheses": [], "keyword_tasks": [task] * 6}

    plan = parse_plan(data, batch=5)

    assert MAX_KEYWORD_TASKS == 4
    assert len(plan.keyword_tasks) == MAX_KEYWORD_TASKS


def test_parse_plan_truncates_hypotheses_to_batch_size() -> None:
    data = {
        "assessment": "",
        "hypotheses": [{"hypothesis_json": _affine_json()}] * 4,
        "keyword_tasks": [],
    }
    assert len(parse_plan(data, batch=2).hypotheses) == 2


def test_heuristic_planner_never_reproposes_a_recorded_hypothesis(store: Store) -> None:
    planner = HeuristicPlanner(pages=("p54-55",))
    first = planner.plan(store, batch=1, feedback=[]).hypotheses[0]
    store.add_hypothesis(first, "heuristic")

    proposed = planner.plan(store, batch=5, feedback=[]).hypotheses
    assert first.fingerprint() not in {h.fingerprint() for h in proposed}


def test_claude_planner_returns_a_plan_from_the_fake_llm(
    llm: LLM, fake_client: FakeClient, store: Store
) -> None:
    reply = {
        "assessment": "affine first",
        "hypotheses": [{"hypothesis_json": _affine_json()}],
        "keyword_tasks": [],
    }
    fake_client.reply(json.dumps(reply))

    plan = ClaudePlanner(llm).plan(store, batch=3, feedback=[])

    assert plan.notes == "affine first"
    assert len(plan.hypotheses) == 1
    assert plan.rejected == []
    assert fake_client.calls[-1]["model"] == "claude-opus-5-5"


def test_claude_planner_reports_llm_failure_as_rejected_message(
    llm: LLM, fake_client: FakeClient, store: Store
) -> None:
    fake_client.reply("{}", stop_reason="refusal")

    plan = ClaudePlanner(llm).plan(store, batch=3, feedback=[])

    assert plan.hypotheses == []
    assert len(plan.rejected) == 1
    assert plan.rejected[0].startswith("planner call failed")


def test_keyword_worker_drops_keys_with_digits_and_builds_vigenere_hypothesis(
    llm: LLM, fake_client: FakeClient
) -> None:
    fake_client.reply(json.dumps({"keys": ["divinity", "ab3", "primes", "primes"]}))
    task = KeywordTask(theme="divinity", page="p54-55", count=40)

    hyps = KeywordWorker(llm).run(task)

    assert len(hyps) == 1
    h = hyps[0]
    assert isinstance(h, H.VigenereKeyH)
    assert h.keys == ["DIVINITY", "PRIMES"]
    assert h.page == "p54-55"


def test_keyword_worker_builds_autokey_hypothesis_for_autokey_tasks(
    llm: LLM, fake_client: FakeClient
) -> None:
    fake_client.reply(json.dumps({"keys": ["emergence"]}))
    task = KeywordTask(theme="emergence", page="p54-55", family="autokey", count=5)

    hyps = KeywordWorker(llm).run(task)

    assert isinstance(hyps[0], H.AutokeyH)
    assert hyps[0].primers == ["EMERGENCE"]


def _store_two_candidates(store: Store) -> list[int]:
    page = corpus.load("p54-55")
    h = H.AffineH(page="p54-55")
    store.add_hypothesis(h, "test")
    cands = [
        Candidate("p54-55", "affine", f"c{i}", page.runes.copy(), scoring.Score(-5.0, 0.5))
        for i in range(2)
    ]
    store.finish(h, cands)
    return [r.id for r in store.top_candidates(10)]


def test_judge_ignores_ids_not_in_the_candidate_list(
    llm: LLM, fake_client: FakeClient, store: Store
) -> None:
    ids = _store_two_candidates(store)
    rows = store.top_candidates(10)
    bogus_id = max(ids) + 1000
    fake_client.reply(
        json.dumps(
            {
                "verdicts": [
                    {"id": ids[0], "score": 0.6, "note": "ok"},
                    {"id": bogus_id, "score": 0.9, "note": "invented"},
                ]
            }
        )
    )

    result = JudgeWorker(llm).run(rows, store)

    assert result == [(ids[0], pytest.approx(0.6))]
    judged = {r.id: r.judge_score for r in store.top_candidates(10)}
    assert judged[ids[0]] == pytest.approx(0.6)
    assert bogus_id not in judged


def test_judge_clamps_scores_into_zero_one(llm: LLM, fake_client: FakeClient, store: Store) -> None:
    ids = _store_two_candidates(store)
    rows = store.top_candidates(10)
    fake_client.reply(
        json.dumps(
            {
                "verdicts": [
                    {"id": ids[0], "score": 1.7, "note": "too high"},
                    {"id": ids[1], "score": -0.4, "note": "too low"},
                ]
            }
        )
    )

    result = dict(JudgeWorker(llm).run(rows, store))

    assert result[ids[0]] == 1.0
    assert result[ids[1]] == 0.0
    judged = {r.id: r.judge_score for r in store.top_candidates(10)}
    assert judged[ids[0]] == 1.0
    assert judged[ids[1]] == 0.0


def test_judge_with_no_candidates_makes_no_llm_call(
    llm: LLM, fake_client: FakeClient, store: Store
) -> None:
    assert JudgeWorker(llm).run([], store) == []
    assert fake_client.calls == []

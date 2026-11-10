"""Sqlite lab notebook: dedup, candidate recording, failures, spend and judgements."""

from __future__ import annotations

import pytest

from lplab import corpus
from lplab import hypotheses as H
from lplab.scoring import Score
from lplab.store import Store


def _cand(page: str, quad: float, words: float, detail: str = "d") -> H.Candidate:
    plaintext = corpus.load(page).runes.copy()
    return H.Candidate(
        page=page,
        family="affine",
        detail=detail,
        plaintext=plaintext,
        score=Score(quad=quad, words=words),
    )


def test_add_hypothesis_is_true_first_then_false_for_a_duplicate(store: Store) -> None:
    h = H.AffineH(page="p54-55")
    assert store.add_hypothesis(h, "test") is True
    assert store.add_hypothesis(h, "test") is False


def test_duplicate_detection_ignores_rationale(store: Store) -> None:
    assert store.add_hypothesis(H.AffineH(page="p54-55", rationale="one"), "test")
    assert not store.add_hypothesis(H.AffineH(page="p54-55", rationale="two"), "test")


def test_finish_records_candidates_and_top_candidates_orders_by_combined(store: Store) -> None:
    h = H.AffineH(page="p54-55")
    store.add_hypothesis(h, "test")
    store.finish(
        h,
        [
            _cand("p54-55", quad=-8.0, words=0.0, detail="low"),
            _cand("p54-55", quad=-4.0, words=0.9, detail="high"),
            _cand("p54-55", quad=-6.0, words=0.4, detail="mid"),
        ],
    )

    rows = store.top_candidates(10)

    assert [r.detail for r in rows] == ["high", "mid", "low"]
    combined = [r.combined for r in rows]
    assert combined == sorted(combined, reverse=True)
    assert store.has(h.fingerprint())


def test_finish_marks_hypothesis_done(store: Store) -> None:
    h = H.AffineH(page="p54-55")
    store.add_hypothesis(h, "test")
    store.finish(h, [_cand("p54-55", quad=-5.0, words=0.5)])
    assert store.counts() == {"done": 1}


def test_fail_sets_status_error_in_counts(store: Store) -> None:
    h = H.AffineH(page="p54-55")
    store.add_hypothesis(h, "test")
    store.fail(h, "boom")
    assert store.counts() == {"error": 1}


def test_record_llm_call_accumulates_total_cost(store: Store) -> None:
    store.record_llm_call("planner", "claude-opus-5-5", 1000, 100, 0, 0.25)
    store.record_llm_call("judge", "claude-haiku-5-5", 500, 50, 0, 0.5)
    assert store.total_cost() == pytest.approx(0.75)


def test_total_cost_is_zero_on_an_empty_store(store: Store) -> None:
    assert store.total_cost() == 0.0


def test_unjudged_promising_then_set_judgement_removes_it_from_the_queue(store: Store) -> None:
    h = H.AffineH(page="p54-55")
    store.add_hypothesis(h, "test")
    store.finish(h, [_cand("p54-55", quad=-4.0, words=0.9)])

    pending = store.unjudged_promising(min_combined=0.0)
    assert len(pending) == 1
    cand_id = pending[0].id

    store.set_judgement(cand_id, 0.7, "reads like English")

    assert store.unjudged_promising(min_combined=0.0) == []
    judged = store.top_candidates(1)[0]
    assert judged.judge_score == pytest.approx(0.7)


def test_unjudged_promising_respects_the_combined_threshold(store: Store) -> None:
    h = H.AffineH(page="p54-55")
    store.add_hypothesis(h, "test")
    store.finish(h, [_cand("p54-55", quad=-8.0, words=0.0)])
    assert store.unjudged_promising(min_combined=0.45) == []


def test_family_summary_counts_done_hypotheses_per_page_and_family(store: Store) -> None:
    h1 = H.AffineH(page="p54-55")
    h2 = H.AffineH(page="p54-55", affine_mode="atbash")
    for h in (h1, h2):
        store.add_hypothesis(h, "test")
        store.finish(h, [_cand("p54-55", quad=-5.0, words=0.5)])
    expected_best = round(Score(quad=-5.0, words=0.5).combined, 4)
    assert store.family_summary() == [
        {"page": "p54-55", "family": "affine", "tried": 2, "best": expected_best}
    ]


def test_candidate_preview_is_stored_as_rendered_text(store: Store) -> None:
    h = H.AffineH(page="p54-55")
    store.add_hypothesis(h, "test")
    store.finish(h, [_cand("p54-55", quad=-5.0, words=0.5)])
    assert store.top_candidates(1)[0].preview == corpus.load("p54-55").render(
        corpus.load("p54-55").runes
    )[:120]

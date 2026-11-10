"""The plan -> execute -> record loop, with the heuristic planner and no LLM."""

from __future__ import annotations

from pathlib import Path

from lplab import corpus
from lplab import hypotheses as H
from lplab.hypotheses import Candidate
from lplab.orchestrator import Orchestrator, RunConfig
from lplab.planner import HeuristicPlanner
from lplab.scoring import Score
from lplab.store import Store


def _orchestrator(store: Store, out_dir: Path) -> Orchestrator:
    return Orchestrator(
        store=store,
        planner=HeuristicPlanner(pages=("p54-55",)),
        out_dir=out_dir,
    )


def test_one_round_runs_and_stores_two_done_hypotheses(store: Store, tmp_path: Path) -> None:
    orch = _orchestrator(store, tmp_path)

    reports = orch.run(RunConfig(rounds=1, batch=2, workers=1))

    assert len(reports) == 1
    assert reports[0].proposed == 2
    assert reports[0].new == 2
    assert store.counts() == {"done": 2}


def test_exhausted_budget_runs_zero_rounds(store: Store, tmp_path: Path) -> None:
    store.record_llm_call("planner", "claude-opus-5-5", 0, 0, 0, 10.0)
    orch = _orchestrator(store, tmp_path)

    reports = orch.run(RunConfig(rounds=1, batch=2, budget_usd=5.0, workers=1))

    assert reports == []
    assert store.counts() == {}


def _seed_judged_hit(store: Store, judge: float = 0.9) -> None:
    page = corpus.load("p54-55")
    seeded = H.AffineH(page="p54-55", affine_mode="atbash")
    store.add_hypothesis(seeded, "test")
    store.finish(
        seeded,
        [Candidate("p54-55", "affine", "seeded", page.runes.copy(), Score(-4.0, 0.9))],
    )
    store.set_judgement(store.top_candidates(1)[0].id, judge, "reads as English")


def test_judged_english_candidate_writes_breakthrough_file(store: Store, tmp_path: Path) -> None:
    _seed_judged_hit(store)
    orch = _orchestrator(store, tmp_path)

    assert orch._breakthrough(since_id=0)

    text = (tmp_path / "BREAKTHROUGH.md").read_text(encoding="utf-8")
    assert "Possible breakthrough" in text
    assert "p54-55 / affine / judge 0.9" in text


def test_hit_from_an_earlier_run_does_not_stop_a_new_run(store: Store, tmp_path: Path) -> None:
    # regression: a stale judged hit used to end every later run after round 1
    _seed_judged_hit(store)
    orch = _orchestrator(store, tmp_path)

    reports = orch.run(RunConfig(rounds=2, batch=1, workers=1))

    assert len(reports) == 2
    assert not (tmp_path / "BREAKTHROUGH.md").exists()


def test_stale_pending_hypotheses_are_rerun(store: Store, tmp_path: Path) -> None:
    # regression: rows left pending by an interrupted run were skipped forever
    first = next(iter(HeuristicPlanner(pages=("p54-55",)).plan(store, 1, []).hypotheses))
    store.add_hypothesis(first, "interrupted run")
    orch = _orchestrator(store, tmp_path)

    orch.run(RunConfig(rounds=1, batch=1, workers=1))

    assert store.counts() == {"done": 1}


class _DuplicatePlanner:
    name = "dupes"

    def __init__(self, h: H.Hypothesis) -> None:
        self.h = h

    def plan(self, store: Store, batch: int, feedback: list[str]):  # type: ignore[no-untyped-def]
        from lplab.planner import Plan

        return Plan(hypotheses=[self.h])


def test_all_duplicate_plan_falls_back_to_curriculum(store: Store, tmp_path: Path) -> None:
    # regression: a plan of only duplicates used to spend a round doing nothing
    done = H.AffineH(page="p54-55", affine_mode="atbash")
    store.add_hypothesis(done, "earlier")
    store.finish(done, [])
    orch = Orchestrator(
        store=store,
        planner=_DuplicatePlanner(done),
        fallback=HeuristicPlanner(pages=("p54-55",)),
        out_dir=tmp_path,
    )

    reports = orch.run(RunConfig(rounds=1, batch=1, workers=1))

    # the planner's only proposal was a duplicate, but the round still ran new curriculum work
    assert reports[0].new == 1
    assert store.counts()["done"] == 2

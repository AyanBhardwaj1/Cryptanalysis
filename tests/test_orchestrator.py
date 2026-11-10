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


def test_judged_english_candidate_writes_breakthrough_file(store: Store, tmp_path: Path) -> None:
    page = corpus.load("p54-55")
    seeded = H.AffineH(page="p54-55", affine_mode="atbash")
    store.add_hypothesis(seeded, "test")
    store.finish(
        seeded,
        [Candidate("p54-55", "affine", "seeded", page.runes.copy(), Score(-4.0, 0.9))],
    )
    store.set_judgement(store.top_candidates(1)[0].id, 0.9, "reads as English")
    orch = _orchestrator(store, tmp_path)

    reports = orch.run(RunConfig(rounds=1, batch=1, workers=1))

    breakthrough = tmp_path / "BREAKTHROUGH.md"
    assert breakthrough.exists()
    text = breakthrough.read_text(encoding="utf-8")
    assert "Possible breakthrough" in text
    assert "p54-55 / affine / judge 0.9" in text
    assert len(reports) == 1

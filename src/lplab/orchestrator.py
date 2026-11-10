"""The all-day loop: plan -> expand -> execute -> judge -> record -> repeat.

Stops on: max rounds, dollar budget, a planner with nothing left to propose, or a candidate the
judge rates as meaningful English (written to ``runs/BREAKTHROUGH.md`` for a human to check).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import runner
from .planner import HeuristicPlanner, Plan, Planner
from .store import Store
from .workers import JudgeWorker, KeywordWorker, run_keyword_tasks

log = logging.getLogger("lplab.orchestrator")

BREAKTHROUGH_JUDGE = 0.8
JUDGE_MIN_COMBINED = 0.45


@dataclass
class RunConfig:
    rounds: int = 10
    batch: int = 8
    budget_usd: float = 5.0
    workers: int | None = None
    top_k: int = 5
    stop_on_breakthrough: bool = True


@dataclass
class RoundReport:
    round: int
    proposed: int
    new: int
    rejected: list[str]
    best: list[str] = field(default_factory=list)
    judged: int = 0
    cost_usd: float = 0.0


@dataclass
class Orchestrator:
    store: Store
    planner: Planner
    keyword_worker: KeywordWorker | None = None
    judge: JudgeWorker | None = None
    fallback: Planner = field(default_factory=HeuristicPlanner)
    out_dir: Path = Path("runs")

    def _plan(self, cfg: RunConfig, feedback: list[str]) -> tuple[Plan, list[str]]:
        plan = self.planner.plan(self.store, cfg.batch, feedback)
        errors = list(plan.rejected)
        if self.keyword_worker and plan.keyword_tasks:
            hyps, errs = run_keyword_tasks(self.keyword_worker, plan.keyword_tasks)
            plan.hypotheses.extend(hyps)
            errors.extend(errs)
        if not plan.hypotheses and self.planner is not self.fallback:
            log.warning("planner produced nothing usable; falling back to %s", self.fallback.name)
            plan = self.fallback.plan(self.store, cfg.batch, feedback)
        return plan, errors

    def run(self, cfg: RunConfig) -> list[RoundReport]:
        reports: list[RoundReport] = []
        feedback: list[str] = []
        for rnd in range(1, cfg.rounds + 1):
            if self.store.total_cost() >= cfg.budget_usd:
                log.info("budget %.2f USD reached; stopping", cfg.budget_usd)
                break
            plan, errors = self._plan(cfg, feedback)
            new = [h for h in plan.hypotheses if self.store.add_hypothesis(h, self.planner.name)]
            dupes = len(plan.hypotheses) - len(new)
            feedback = errors + ([f"{dupes} proposed hypotheses were duplicates"] if dupes else [])
            if not new and not plan.hypotheses:
                log.info("nothing left to try; stopping")
                break
            t0 = time.time()
            outcomes = runner.run(new, self.store, workers=cfg.workers, top_k=cfg.top_k)
            feedback += [f"{o.hypothesis.family} failed: {o.error}" for o in outcomes if o.error]
            report = RoundReport(rnd, len(plan.hypotheses), len(new), errors)
            report.best = [
                f"{c.page} {c.family} {c.combined:.3f} | {c.detail[:80]}"
                for c in self.store.top_candidates(3)
            ]
            if self.judge:
                report.judged = self._judge(feedback)
            report.cost_usd = round(self.store.total_cost(), 4)
            reports.append(report)
            log.info(
                "round %d: %d new hypotheses in %.1fs, spend $%.4f, best: %s",
                rnd, len(new), time.time() - t0, report.cost_usd,
                report.best[0] if report.best else "-",
            )  # fmt: skip
            if cfg.stop_on_breakthrough and self._breakthrough():
                log.warning("possible breakthrough written to %s", self.out_dir / "BREAKTHROUGH.md")
                break
        return reports

    def _judge(self, feedback: list[str]) -> int:
        from .llm import LLMError

        assert self.judge is not None
        pending = self.store.unjudged_promising(JUDGE_MIN_COMBINED, n=10)
        try:
            return len(self.judge.run(pending, self.store))
        except LLMError as e:
            feedback.append(f"judge failed: {e}")
            return 0

    def _breakthrough(self) -> bool:
        hits = [
            c
            for c in self.store.top_candidates(50)
            if c.judge_score is not None and c.judge_score >= BREAKTHROUGH_JUDGE
        ]
        if not hits:
            return False
        self.out_dir.mkdir(parents=True, exist_ok=True)
        lines = ["# Possible breakthrough (verify by hand before celebrating)", ""]
        for c in hits:
            lines.append(
                f"- {c.page} / {c.family} / judge {c.judge_score} / combined {c.combined:.3f}"
            )
            lines.append(f"  - {c.detail}")
            lines.append(f"  - `{c.preview}`")
        (self.out_dir / "BREAKTHROUGH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (self.out_dir / "breakthrough.json").write_text(
            json.dumps([c.__dict__ for c in hits], indent=2), encoding="utf-8"
        )
        return True

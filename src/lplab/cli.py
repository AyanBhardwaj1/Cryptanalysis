"""Command line entry point: ``lplab <command>``."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

from . import corpus, kernels, stats
from . import hypotheses as H


def _cmd_stats(args: argparse.Namespace) -> int:
    pages = [args.page] if args.page else list(corpus.UNSOLVED)
    print(f"{'page':<20}{'len':>6}{'IoC':>8}{'H(bits)':>9}{'doublet':>9}{'p(doub)':>10}{'per':>5}")
    for name in pages:
        f = stats.fingerprint(corpus.load(name).runes)
        print(
            f"{name:<20}{f.length:>6}{f.ioc:>8.3f}{f.entropy:>9.3f}{f.doublet_rate:>9.4f}"
            f"{f.doublet_pvalue:>10.1e}{f.best_period:>5}"
        )
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    from .solutions import RECIPES

    failures = 0
    for name, h in RECIPES.items():
        best = H.execute(h, top_k=1)[0]
        truth = corpus.load_solution(name).runes
        ok = bool(np.array_equal(best.plaintext, truth))
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<20} {best.detail}")
    print(f"{len(RECIPES) - failures}/{len(RECIPES)} solved sections reproduced")
    return 1 if failures else 0


def _cmd_attack(args: argparse.Namespace) -> int:
    raw = (
        Path(args.hypothesis[1:]).read_text()
        if args.hypothesis.startswith("@")
        else args.hypothesis
    )
    h = H.parse(raw)
    for c in H.execute(h, top_k=args.top):
        print(json.dumps(c.as_dict(), ensure_ascii=False))
    return 0


def _cmd_top(args: argparse.Namespace) -> int:
    from .store import Store

    store = Store(Path(args.db))
    for c in store.top_candidates(args.n, page=args.page):
        judge = "-" if c.judge_score is None else f"{c.judge_score:.2f}"
        print(f"{c.combined:.3f} q={c.quad:.2f} w={c.words:.2f} j={judge} {c.page} {c.family}")
        print(f"    {c.detail}")
        print(f"    {c.preview[:110]!r}")
    print(json.dumps(store.counts()), f"spend=${store.total_cost():.4f}")
    return 0


def _cmd_orchestrate(args: argparse.Namespace) -> int:
    from .llm import LLM
    from .orchestrator import Orchestrator, RunConfig
    from .planner import ClaudePlanner, HeuristicPlanner
    from .store import Store
    from .workers import JudgeWorker, KeywordWorker

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    store = Store(Path(args.db))
    llm = LLM(store, budget_usd=args.budget)
    use_claude = args.planner == "claude"
    orch = Orchestrator(
        store=store,
        planner=ClaudePlanner(llm) if use_claude else HeuristicPlanner(),
        keyword_worker=KeywordWorker(llm) if use_claude else None,
        judge=JudgeWorker(llm) if (use_claude or args.judge) else None,
        out_dir=Path(args.db).parent,
    )
    cfg = RunConfig(
        rounds=args.rounds,
        batch=args.batch,
        budget_usd=args.budget,
        workers=args.workers,
        stop_on_breakthrough=not args.keep_going,
    )
    reports = orch.run(cfg)
    for r in reports:
        print(f"round {r.round}: {r.new}/{r.proposed} new, judged {r.judged}, ${r.cost_usd}")
        for line in r.best[:1]:
            print(f"   best: {line}")
        for err in r.rejected[:5]:
            print(f"   rejected: {err}")
    return 0


def _cmd_crib(args: argparse.Namespace) -> int:
    """Keystream that would turn the ciphertext at a position into a guessed plaintext."""
    from .gematria import indices_to_latin, latin_to_indices
    from .known_plaintext import keystream_from_pair

    page = corpus.load(args.page)
    guess = latin_to_indices(args.text)
    ct = page.runes[args.position : args.position + guess.size]
    if ct.size != guess.size:
        print("crib runs past the end of the page", file=sys.stderr)
        return 2
    k = keystream_from_pair(ct, guess, sign=args.sign)
    print("key indices:", k.tolist())
    print("key latin:  ", indices_to_latin(k))
    return 0


def _cmd_screen(args: argparse.Namespace) -> int:
    from . import simulate

    obs = simulate.observed()
    print(f"observed unsolved pages: IoC={obs.ioc:.3f} doublet={obs.doublet_rate:.4f}")
    print(f"{'mechanism':<30}{'IoC':>7}{'doublet':>10}{'sd':>8}  fits")
    for r in simulate.screen(trials=args.trials, length=args.length):
        fits = "yes" if r.matches_observed else "no"
        print(f"{r.mechanism:<30}{r.ioc:>7.3f}{r.doublet_rate:>10.4f}{r.doublet_sd:>8.4f}  {fits}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from . import report

    out = report.write(Path(args.out), Path(args.db), trials=args.trials)
    print(f"wrote {out}")
    return 0


def _cmd_build_kernel(args: argparse.Namespace) -> int:
    path = kernels.build(force=True)
    print(f"built {path} (backend: {kernels.backend()})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="lplab", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stats", help="statistical fingerprints of pages")
    p.add_argument("--page")
    p.set_defaults(fn=_cmd_stats)

    p = sub.add_parser("verify", help="reproduce every solved section through the search path")
    p.set_defaults(fn=_cmd_verify)

    p = sub.add_parser("attack", help="run one hypothesis (JSON string or @file)")
    p.add_argument("hypothesis")
    p.add_argument("--top", type=int, default=5)
    p.set_defaults(fn=_cmd_attack)

    p = sub.add_parser("top", help="best candidates found so far")
    p.add_argument("-n", type=int, default=10)
    p.add_argument("--page")
    p.add_argument("--db", default="runs/lab.sqlite")
    p.set_defaults(fn=_cmd_top)

    p = sub.add_parser("orchestrate", help="the planning/search loop")
    p.add_argument("--planner", choices=("claude", "heuristic"), default="heuristic")
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--budget", type=float, default=5.0, help="max LLM spend in USD")
    p.add_argument("--workers", type=int, default=None, help="search processes")
    p.add_argument("--judge", action="store_true", help="Haiku judge with heuristic planner")
    p.add_argument(
        "--keep-going", action="store_true", help="don't stop when the judge flags a candidate"
    )
    p.add_argument("--db", default="runs/lab.sqlite")
    p.set_defaults(fn=_cmd_orchestrate)

    p = sub.add_parser("crib", help="keystream implied by a plaintext guess")
    p.add_argument("--page", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--position", type=int, default=0)
    p.add_argument("--sign", type=int, choices=(1, -1), default=1)
    p.set_defaults(fn=_cmd_crib)

    p = sub.add_parser("screen", help="which cipher mechanisms reproduce the page statistics")
    p.add_argument("--trials", type=int, default=30)
    p.add_argument("--length", type=int, default=1500)
    p.set_defaults(fn=_cmd_screen)

    p = sub.add_parser("report", help="HTML report: anomaly charts, screen, best candidates")
    p.add_argument("--out", default="runs/report.html")
    p.add_argument("--db", default="runs/lab.sqlite")
    p.add_argument("--trials", type=int, default=20)
    p.set_defaults(fn=_cmd_report)

    p = sub.add_parser("build-kernel", help="(re)compile the C kernel")
    p.set_defaults(fn=_cmd_build_kernel)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())

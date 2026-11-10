"""Execute hypotheses in parallel worker processes and persist the results."""

from __future__ import annotations

import os
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass

from .hypotheses import Candidate, Hypothesis, execute, parse
from .store import Store


@dataclass(frozen=True)
class Outcome:
    hypothesis: Hypothesis
    candidates: tuple[Candidate, ...]
    error: str | None = None


def _run_one(payload: dict[str, object], top_k: int) -> tuple[dict[str, object], list[Candidate]]:
    # re-validate inside the worker: only plain data crosses the process boundary
    h = parse(payload)
    return payload, execute(h, top_k=top_k)


def run(
    hypotheses: Sequence[Hypothesis],
    store: Store,
    *,
    workers: int | None = None,
    top_k: int = 5,
) -> list[Outcome]:
    """Run each hypothesis once, record candidates (or the error) in ``store``."""
    if not hypotheses:
        return []
    n = workers if workers is not None else max(1, (os.cpu_count() or 2) - 1)
    by_fp = {h.fingerprint(): h for h in hypotheses}
    outcomes: list[Outcome] = []
    if n == 1:
        for h in hypotheses:
            outcomes.append(_safe_local(h, store, top_k))
        return outcomes
    with ProcessPoolExecutor(max_workers=n) as pool:
        futures = {pool.submit(_run_one, h.model_dump(), top_k): fp for fp, h in by_fp.items()}
        for fut in as_completed(futures):
            h = by_fp[futures[fut]]
            try:
                _payload, cands = fut.result()
            except BrokenProcessPool as e:
                # infrastructure failure (OOM kill, Ctrl-C): leave the row pending so it re-runs
                outcomes.append(Outcome(h, (), f"worker pool broken, will retry: {e}"))
                continue
            except Exception as e:
                store.fail(h, f"{type(e).__name__}: {e}")
                outcomes.append(Outcome(h, (), f"{type(e).__name__}: {e}"))
                continue
            store.finish(h, cands)
            outcomes.append(Outcome(h, tuple(cands)))
    return outcomes


def _safe_local(h: Hypothesis, store: Store, top_k: int) -> Outcome:
    try:
        cands = execute(h, top_k=top_k)
    except Exception as e:
        store.fail(h, f"{type(e).__name__}: {e}")
        return Outcome(h, (), f"{type(e).__name__}: {e}")
    store.finish(h, cands)
    return Outcome(h, tuple(cands))

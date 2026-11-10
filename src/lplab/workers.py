"""Haiku workers: cheap, parallel, narrow jobs for the orchestrator.

* :class:`KeywordWorker` brainstorms candidate keys on a theme -> hypotheses.
* :class:`JudgeWorker` reads the best statistical candidates and rates whether they are
  meaningful English (a statistical score can be fooled by repetitive or degenerate text).

Each worker's output is schema-validated and clamped before the orchestrator uses it.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from . import hypotheses as H
from .llm import LLM, WORKER_MODEL, LLMError
from .planner import KeywordTask
from .store import CandidateRow, Store

_KEY_RE = re.compile(r"^[A-Za-z ]{1,80}$")

KEYWORD_SYSTEM = """You generate candidate cipher keys for a Liber Primus (Cicada 3301) \
cryptanalysis lab. Keys are English words or short phrases (letters and spaces only, max 80 \
chars) that the puzzle authors might plausibly have used: drawn from the given theme, Cicada \
3301 vocabulary (primes, divinity, circumference, instar, emergence, koans, self-reliance, \
the deep web), mysticism, philosophy and cryptography. Return distinct keys, most plausible \
first. Do not explain."""

KEYWORD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"keys": {"type": "array", "items": {"type": "string"}}},
    "required": ["keys"],
    "additionalProperties": False,
}

JUDGE_SYSTEM = """You judge candidate decryptions from a cryptanalysis lab. Each candidate is \
a transliteration of runes into Latin letters using LP spelling (TH, NG, EO, OE, AE, IA, EA are \
single runes; U stands for V; C for K). Rate each from 0.0 to 1.0: 1.0 = clearly meaningful \
English prose, 0.5 = fragments of real words in a plausible order, 0.0 = gibberish or \
repetitive filler. Statistical artefacts (the same short word repeated, letter salad that \
happens to contain common bigrams) get low scores. Be strict; false positives waste hours."""

JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "score": {"type": "number"},
                    "note": {"type": "string"},
                },
                "required": ["id", "score", "note"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["verdicts"],
    "additionalProperties": False,
}


@dataclass
class KeywordWorker:
    llm: LLM
    model: str = WORKER_MODEL

    def run(self, task: KeywordTask) -> list[H.Hypothesis]:
        data = self.llm.json_call(
            role="keyword_worker", model=self.model, system=KEYWORD_SYSTEM,
            user=f"Theme: {task.theme}\nTarget page: {task.page}\nReturn up to {task.count} keys.",
            schema=KEYWORD_SCHEMA, effort="low", max_tokens=4000,
        )  # fmt: skip
        keys = list(
            dict.fromkeys(k.strip().upper() for k in data.get("keys", []) if isinstance(k, str))
        )
        keys = [k for k in keys if _KEY_RE.match(k)][: task.count]
        if not keys:
            return []
        rationale = f"worker keywords: {task.theme}"[:600]
        if task.family == "autokey":
            return [H.AutokeyH(page=task.page, primers=keys, rationale=rationale)]
        return [
            H.VigenereKeyH(page=task.page, keys=keys, affine_mode="shifts", rationale=rationale)
        ]


@dataclass
class JudgeWorker:
    llm: LLM
    model: str = WORKER_MODEL

    def run(self, candidates: Sequence[CandidateRow], store: Store) -> list[tuple[int, float]]:
        if not candidates:
            return []
        listing = "\n".join(f"[{c.id}] {c.preview.replace(chr(10), ' ')}" for c in candidates)
        data = self.llm.json_call(
            role="judge", model=self.model, system=JUDGE_SYSTEM,
            user=f"Rate each candidate by id:\n{listing}",
            schema=JUDGE_SCHEMA, effort="low", max_tokens=4000,
        )  # fmt: skip
        valid = {c.id for c in candidates}
        out: list[tuple[int, float]] = []
        for v in data.get("verdicts", []):
            if not isinstance(v, dict) or v.get("id") not in valid:
                continue  # ignore ids the judge invented
            score = min(1.0, max(0.0, float(v.get("score", 0.0))))
            store.set_judgement(int(v["id"]), score, str(v.get("note", "")))
            out.append((int(v["id"]), score))
        return out


def run_keyword_tasks(
    worker: KeywordWorker, tasks: Sequence[KeywordTask], max_parallel: int = 4
) -> tuple[list[H.Hypothesis], list[str]]:
    """Fan keyword tasks out to Haiku in parallel. Returns (hypotheses, errors)."""
    hyps: list[H.Hypothesis] = []
    errors: list[str] = []
    if not tasks:
        return hyps, errors
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        for task, fut in [(t, pool.submit(worker.run, t)) for t in tasks]:
            try:
                hyps.extend(fut.result())
            except LLMError as e:
                errors.append(f"keyword task '{task.theme[:60]}' failed: {e}")
    return hyps, errors

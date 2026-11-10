"""SQLite lab notebook: hypotheses tried, best candidates, and LLM spend.

Everything the orchestrator knows between rounds (and between days) lives here, so a long run
can be stopped and resumed and the same hypothesis is never executed twice.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .gematria import indices_to_runes
from .hypotheses import Candidate, Hypothesis

DEFAULT_DB = Path("runs") / "lab.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS hypotheses (
    fp TEXT PRIMARY KEY,
    page TEXT NOT NULL,
    family TEXT NOT NULL,
    params TEXT NOT NULL,
    source TEXT NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    best_combined REAL,
    created_at REAL NOT NULL,
    finished_at REAL
);
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fp TEXT NOT NULL REFERENCES hypotheses(fp),
    page TEXT NOT NULL,
    family TEXT NOT NULL,
    detail TEXT NOT NULL,
    quad REAL NOT NULL,
    words REAL NOT NULL,
    combined REAL NOT NULL,
    preview TEXT NOT NULL,
    plaintext TEXT NOT NULL,
    judge_score REAL,
    judge_note TEXT
);
CREATE INDEX IF NOT EXISTS idx_cand_combined ON candidates(combined DESC);
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    role TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_read_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL
);
"""


@dataclass(frozen=True)
class CandidateRow:
    id: int
    page: str
    family: str
    detail: str
    quad: float
    words: float
    combined: float
    preview: str
    judge_score: float | None


class Store:
    def __init__(self, path: Path = DEFAULT_DB) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        with self._conn:
            yield self._conn

    # --- hypotheses ---
    def add_hypothesis(self, h: Hypothesis, source: str) -> bool:
        """Insert if new. Returns False when an identical hypothesis was already recorded."""
        params = h.model_dump(exclude={"rationale"})
        with self._tx() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO hypotheses (fp, page, family, params, source, rationale,"
                " created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (h.fingerprint(), h.page, h.family, json.dumps(params, sort_keys=True), source,
                 h.rationale, time.time()),
            )  # fmt: skip
            return cur.rowcount == 1

    def has(self, fp: str) -> bool:
        row = self._conn.execute("SELECT 1 FROM hypotheses WHERE fp = ?", (fp,)).fetchone()
        return row is not None

    def finish(self, h: Hypothesis, candidates: Sequence[Candidate]) -> None:
        best = max((c.score.combined for c in candidates), default=None)
        with self._tx() as c:
            c.execute(
                "UPDATE hypotheses SET status='done', best_combined=?, finished_at=? WHERE fp=?",
                (best, time.time(), h.fingerprint()),
            )
            c.executemany(
                "INSERT INTO candidates (fp, page, family, detail, quad, words, combined,"
                " preview, plaintext) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (h.fingerprint(), x.page, x.family, x.detail, x.score.quad, x.score.words,
                     x.score.combined, x.preview(), indices_to_runes(x.plaintext))
                    for x in candidates
                ],
            )  # fmt: skip

    def fail(self, h: Hypothesis, error: str) -> None:
        with self._tx() as c:
            c.execute(
                "UPDATE hypotheses SET status='error', error=?, finished_at=? WHERE fp=?",
                (error[:2000], time.time(), h.fingerprint()),
            )

    def counts(self) -> dict[str, int]:
        rows = self._conn.execute("SELECT status, COUNT(*) FROM hypotheses GROUP BY status")
        return {s: n for s, n in rows}

    def family_summary(self) -> list[dict[str, Any]]:
        """Per (page, family): how many hypotheses ran and the best combined score."""
        rows = self._conn.execute(
            "SELECT page, family, COUNT(*), MAX(best_combined) FROM hypotheses"
            " WHERE status='done' GROUP BY page, family ORDER BY page, family"
        )
        return [
            {"page": p, "family": f, "tried": n, "best": round(b or 0.0, 4)} for p, f, n, b in rows
        ]

    def recent_params(self, limit: int = 40) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT params, best_combined FROM hypotheses WHERE status='done'"
            " ORDER BY finished_at DESC LIMIT ?",
            (limit,),
        )
        return [{**json.loads(p), "best": round(b or 0.0, 4)} for p, b in rows]

    # --- candidates ---
    def top_candidates(self, n: int = 10, page: str | None = None) -> list[CandidateRow]:
        sql = (
            "SELECT id, page, family, detail, quad, words, combined, preview, judge_score"
            " FROM candidates"
        )
        args: tuple[Any, ...] = ()
        if page:
            sql += " WHERE page = ?"
            args = (page,)
        sql += " ORDER BY combined DESC LIMIT ?"
        rows = self._conn.execute(sql, (*args, n)).fetchall()
        return [CandidateRow(*r) for r in rows]

    def unjudged_promising(self, min_combined: float, n: int = 10) -> list[CandidateRow]:
        rows = self._conn.execute(
            "SELECT id, page, family, detail, quad, words, combined, preview, judge_score"
            " FROM candidates WHERE judge_score IS NULL AND combined >= ?"
            " ORDER BY combined DESC LIMIT ?",
            (min_combined, n),
        ).fetchall()
        return [CandidateRow(*r) for r in rows]

    def set_judgement(self, cand_id: int, score: float, note: str) -> None:
        with self._tx() as c:
            c.execute(
                "UPDATE candidates SET judge_score=?, judge_note=? WHERE id=?",
                (score, note[:1000], cand_id),
            )

    # --- llm spend ---
    def record_llm_call(
        self, role: str, model: str, inp: int, out: int, cache_read: int, cost: float
    ) -> None:
        with self._tx() as c:
            c.execute(
                "INSERT INTO llm_calls (ts, role, model, input_tokens, output_tokens,"
                " cache_read_tokens, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (time.time(), role, model, inp, out, cache_read, cost),
            )

    def total_cost(self) -> float:
        row = self._conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM llm_calls").fetchone()
        return float(row[0])

"""Planners decide what to try next.

* :class:`HeuristicPlanner` walks a fixed curriculum of attacks over every unsolved page. It
  needs no API key and is the fallback that keeps a run going when the LLM is unavailable.
* :class:`ClaudePlanner` gives the lab notebook (fingerprints, what was tried, best candidates,
  last round's validation errors) to Opus and asks for the next batch as JSON. Its output is
  validated against :mod:`lplab.hypotheses`; anything invalid is rejected and fed back.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import cache
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import corpus, lore, stats
from . import hypotheses as H
from .ciphers import SEQUENCES
from .llm import LLM, PLANNER_MODEL, LLMError
from .store import Store

MAX_KEYWORD_TASKS = 4


class KeywordTask(BaseModel):
    """A request for a Haiku worker to brainstorm key material on a theme."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    theme: str = Field(min_length=3, max_length=300)
    page: H.PageName
    family: Literal["vigenere_key", "autokey"] = "vigenere_key"
    count: int = Field(40, ge=5, le=100)


@dataclass
class Plan:
    hypotheses: list[H.Hypothesis] = field(default_factory=list)
    keyword_tasks: list[KeywordTask] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    notes: str = ""


class Planner(Protocol):
    name: str

    def plan(self, store: Store, batch: int, feedback: list[str]) -> Plan: ...


def page_fingerprints(pages: tuple[str, ...] = corpus.UNSOLVED) -> dict[str, dict[str, Any]]:
    out = {}
    for name in pages:
        fp = stats.fingerprint(corpus.load(name).runes).as_dict()
        out[name] = {k: round(v, 4) if isinstance(v, float) else v for k, v in fp.items()}
    return out


# --- heuristic curriculum ---------------------------------------------------------------


def curriculum(pages: tuple[str, ...] = corpus.UNSOLVED) -> Iterator[H.Hypothesis]:
    """Every attack the lab knows, cheapest first, for every page."""
    keys = list(lore.seed_keys())
    chunks = [keys[i : i + 50] for i in range(0, len(keys), 50)]
    other_sources = corpus.SOLVED + corpus.UNSOLVED
    for page in pages:
        yield H.AffineH(page=page, rationale="curriculum: all 812 affine maps")
    for page in pages:  # skip-if-same keystreams: the only screened family matching the doublets
        for sign in (1, -1):
            for name in SEQUENCES:
                yield H.SkipRuleH(
                    page=page, key_source="sequence", sequence=name, offset_max=20, sign=sign,
                    rationale="curriculum: number stream + skip-if-same rule",
                )  # fmt: skip
            for chunk in [keys[i : i + 30] for i in range(0, len(keys), 30)]:
                yield H.SkipRuleH(
                    page=page, key_source="keyword", keys=chunk, sign=sign,
                    rationale="curriculum: lore keyword + skip-if-same rule",
                )  # fmt: skip
            for src in corpus.SOLVED:
                yield H.SkipRuleH(
                    page=page, key_source="running", source=src, offset_max=200, sign=sign,
                    rationale="curriculum: LP-text running key + skip-if-same rule",
                )  # fmt: skip
    for page in pages:  # ciphertext-feedback / reversed reading (doublet-deficit candidates)
        for t in ("delta", "delta_sum", "reverse"):
            yield H.AffineH(page=page, transform=t, rationale=f"curriculum: {t} view, affine")
            for sign in (1, -1):
                yield H.VigenereClimbH(
                    page=page, transform=t, period_min=1, period_max=30, sign=sign,
                    rationale=f"curriculum: {t} view, periodic key",
                )  # fmt: skip
    for page in pages:
        for sign in (1, -1):
            for name in SEQUENCES:
                yield H.SequenceH(
                    page=page, name=name, offset_max=40, sign=sign, affine_mode="shifts",
                    rationale="curriculum: number-theoretic keystream (cf. p56 totient)",
                )  # fmt: skip
            for chunk in chunks:
                yield H.VigenereKeyH(
                    page=page, keys=chunk, sign=sign, affine_mode="shifts",
                    rationale="curriculum: lore keywords with interrupters",
                )  # fmt: skip
    for page in pages:
        for sign in (1, -1):
            for mode in ("identity", "atbash"):
                yield H.VigenereClimbH(
                    page=page, period_min=1, period_max=60, sign=sign, affine_mode=mode,
                    rationale="curriculum: periodic key hill-climb",
                )  # fmt: skip
    for page in pages:
        for sign in (1, -1):
            for fb in ("plain", "cipher"):
                for chunk in chunks:
                    yield H.AutokeyH(
                        page=page, primers=chunk, feedback=fb, sign=sign,
                        rationale="curriculum: autokey (explains the doublet deficit if feedback)",
                    )  # fmt: skip
            for src in other_sources:
                if src == page:
                    continue
                kinds = ("plaintext", "ciphertext") if src in corpus.SOLVED else ("ciphertext",)
                for kind in kinds:
                    yield H.RunningKeyH(
                        page=page, source=src, source_kind=kind, sign=sign,
                        interrupt_mode="none",
                        rationale="curriculum: running key from another LP section",
                    )  # fmt: skip


@dataclass
class HeuristicPlanner:
    name: str = "heuristic"
    pages: tuple[str, ...] = corpus.UNSOLVED

    def plan(self, store: Store, batch: int, feedback: list[str]) -> Plan:
        out: list[H.Hypothesis] = []
        for h in curriculum(self.pages):
            if not store.has(h.fingerprint()):
                out.append(h)
            if len(out) >= batch:
                break
        return Plan(hypotheses=out, notes="curriculum exhausted" if not out else "")


# --- Claude planner -------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the principal investigator of a cryptanalysis lab attacking the \
unsolved pages of Cicada 3301's Liber Primus (LP). You plan; deterministic code executes.

Facts established by the lab (verified by regression tests against the solved pages):
- Text is in the 29-rune Gematria Primus. Indices 0..28: F U TH O R C G W H N I J EO P X S T B \
E M L NG OE D A AE Y IA EA. Each rune also has a prime value (2,3,5,...,109).
- Every solved LP cipher fits: x = (c - sign*k_j) mod 29, p = (a*x + b) mod 29, where some \
occurrences of an "interrupter" rune (always F so far) pass through and don't advance the key. \
Solved examples: atbash (a=28,b=28); atbash+shift (a=28,b=2); Vigenere key DIVINITY; Vigenere key \
FIRFUMFERENFE; keystream phi(prime_j) = prime_j - 1 (page "An End").
- Unsolved pages have IoC ~1.0 (flat, like a non-periodic key) and a strong doublet deficit: \
adjacent equal runes occur ~0.66% vs 3.45% expected. Any proposal should explain that anomaly or \
test something that could.
- Doublets are suppressed on the ciphertext, not the key: no plaintext-independent additive \
key can go below ~1.3% doublets on English. In the lab's mechanism screen only a keystream with \
a skip-if-same rule (when c would equal the previous rune, burn a key element and re-encrypt) \
firing with probability ~0.81 fits (family "skip_rule"); a periodic key raises IoC above the \
observed 1.00, so favour non-periodic keystreams. Screen results are in mechanism_screen.
- Every one-rune word in solved LP plaintext is A or I; the word score enforces this.
- Community ledgers (2026) report exhaustive negative sweeps of plain additive families: \
OEIS sequences, PRNG seeds, ~200 books as running keys, autokey lag <= 8, periods <= 400. Plain \
(no skip rule) versions of those are low value; combine them with skip_rule or transforms.
- Unsolved pages: 15.5% two-rune words (English ~23%), suggesting possible filler runes.
- Word boundaries survive encryption; candidates are scored by quadgram fitness ("quad", \
English ~ -4.2, random ~ -8.4) and dictionary hit rate over the original word breaks ("words", \
English > 0.8, random < 0.15). "combined" averages the two on a 0..1 scale.

You may only propose hypotheses from the registered families. Each hypothesis is one JSON object \
(sent as a string in hypothesis_json) that must validate against this JSON Schema:
{schema}

Rules:
- Never repeat a hypothesis already listed in recent_tried; change at least one parameter.
- Keep compute sane: vigenere_climb period ranges <= 30 wide; affine_mode "all" only with few keys.
- Use keyword_tasks to ask cheap worker models to brainstorm key words/phrases on a specific \
theme for a specific page; the lab turns them into hypotheses for you.
- Prefer hypotheses that discriminate between explanations over shotgun guessing. Say why in \
each hypothesis's "rationale".
- If last round had validation errors (feedback), fix them."""

PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "assessment": {"type": "string"},
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"hypothesis_json": {"type": "string"}},
                "required": ["hypothesis_json"],
                "additionalProperties": False,
            },
        },
        "keyword_tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string"},
                    "page": {"type": "string"},
                    "family": {"type": "string", "enum": ["vigenere_key", "autokey"]},
                    "count": {"type": "integer"},
                },
                "required": ["theme", "page", "family", "count"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["assessment", "hypotheses", "keyword_tasks"],
    "additionalProperties": False,
}


@cache
def _screen_summary() -> list[dict[str, Any]]:
    from . import simulate

    return [
        {"mechanism": r.mechanism, "doublet": round(r.doublet_rate, 4), "ioc": round(r.ioc, 3)}
        for r in simulate.screen(trials=10, length=1200)
    ]


def lab_context(store: Store, feedback: list[str], batch: int) -> dict[str, Any]:
    return {
        "batch_size": batch,
        "pages": page_fingerprints(),
        "tried_summary": store.family_summary(),
        "recent_tried": store.recent_params(40),
        "best_candidates": [
            {
                "page": c.page, "family": c.family, "detail": c.detail,
                "quad": round(c.quad, 3), "words": round(c.words, 3),
                "combined": round(c.combined, 3), "judge": c.judge_score,
                "preview": c.preview[:100],
            }
            for c in store.top_candidates(10)
        ],
        "mechanism_screen": _screen_summary(),
        "feedback": feedback[-20:],
        "llm_spend_usd": round(store.total_cost(), 4),
    }  # fmt: skip


def parse_plan(data: dict[str, Any], batch: int) -> Plan:
    """Validate the planner's raw JSON. Invalid items are rejected with a reason, not dropped."""
    plan = Plan(notes=str(data.get("assessment", ""))[:2000])
    for item in list(data.get("hypotheses", []))[: batch * 2]:
        raw = item.get("hypothesis_json", "") if isinstance(item, dict) else ""
        try:
            plan.hypotheses.append(H.parse(raw))
        except ValidationError as e:
            plan.rejected.append(f"{raw[:200]} -> {e.errors()[0]['msg']}")
        except (ValueError, TypeError) as e:
            plan.rejected.append(f"{raw[:200]} -> {e}")
    for task in list(data.get("keyword_tasks", []))[:MAX_KEYWORD_TASKS]:
        try:
            plan.keyword_tasks.append(KeywordTask.model_validate(task))
        except ValidationError as e:
            plan.rejected.append(f"keyword_task {json.dumps(task)[:200]} -> {e.errors()[0]['msg']}")
    plan.hypotheses = plan.hypotheses[:batch]
    return plan


@dataclass
class ClaudePlanner:
    llm: LLM
    name: str = "claude"
    model: str = PLANNER_MODEL
    effort: str = "high"

    def plan(self, store: Store, batch: int, feedback: list[str]) -> Plan:
        system = SYSTEM_PROMPT.replace("{schema}", json.dumps(H.json_schema(), sort_keys=True))
        user = "Lab notebook (JSON). Propose the next batch.\n" + json.dumps(
            lab_context(store, feedback, batch), sort_keys=True
        )
        try:
            data = self.llm.json_call(
                role="planner", model=self.model, system=system, user=user,
                schema=PLAN_SCHEMA, effort=self.effort,
            )  # fmt: skip
        except LLMError as e:
            return Plan(rejected=[f"planner call failed: {e}"])
        return parse_plan(data, batch)

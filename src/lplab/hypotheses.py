"""Registry of attack families.

A *hypothesis* is a validated pydantic object naming a cipher family, a page and bounded
parameters. The orchestrator (or a human, or the heuristic planner) proposes hypotheses as
JSON; :func:`parse` validates them against this registry and :func:`execute` runs them with
the deterministic search code. Nothing proposed by an LLM is ever executed as code, and every
numeric parameter is capped so one hypothesis can't monopolise the machine.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import Annotated, Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from . import ciphers as C
from . import corpus, kernels, ngram, scoring
from .gematria import IndexArray, N, indices_to_latin, latin_to_indices

AffineMode = Literal["identity", "atbash", "shifts", "all"]
InterruptMode = Literal["none", "all", "greedy"]
Transform = Literal["none", "delta", "delta_sum", "reverse"]
PageName = corpus.PageName

KeyWord = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[A-Za-z ]+$")]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    page: PageName
    sign: Literal[1, -1] = 1
    affine_mode: AffineMode = "identity"
    interrupter: int | None = Field(0, ge=0, le=N - 1)
    interrupt_mode: InterruptMode = "greedy"
    transform: Transform = "none"
    rationale: str = Field("", max_length=600)

    def fingerprint(self) -> str:
        """Stable hash of the parameters (rationale excluded) used to dedupe hypotheses."""
        body = self.model_dump(exclude={"rationale"})
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:20]


class AffineH(_Base):
    family: Literal["affine"] = "affine"
    affine_mode: AffineMode = "all"
    interrupter: int | None = Field(None, ge=0, le=N - 1)
    interrupt_mode: InterruptMode = "none"


class VigenereKeyH(_Base):
    family: Literal["vigenere_key"] = "vigenere_key"
    keys: list[KeyWord] = Field(min_length=1, max_length=200)


class VigenereClimbH(_Base):
    family: Literal["vigenere_climb"] = "vigenere_climb"
    period_min: int = Field(1, ge=1, le=120)
    period_max: int = Field(30, ge=1, le=120)
    restarts: int = Field(8, ge=1, le=64)
    affine_mode: Literal["identity", "atbash"] = "identity"

    @field_validator("period_max")
    @classmethod
    def _order(cls, v: int, info: Any) -> int:
        if v < info.data.get("period_min", 1):
            raise ValueError("period_max must be >= period_min")
        return v


class SequenceH(_Base):
    family: Literal["sequence"] = "sequence"
    name: C.SequenceName
    offset_max: int = Field(0, ge=0, le=500)


class AutokeyH(_Base):
    family: Literal["autokey"] = "autokey"
    primers: list[KeyWord] = Field(min_length=1, max_length=100)
    feedback: Literal["plain", "cipher"] = "plain"


class RunningKeyH(_Base):
    family: Literal["running_key"] = "running_key"
    source: PageName
    source_kind: Literal["plaintext", "ciphertext"] = "plaintext"


class SkipRuleH(_Base):
    """Keystream + skip-if-same rule (see :mod:`lplab.skiprule`): the doublet-deficit model."""

    family: Literal["skip_rule"] = "skip_rule"
    key_source: Literal["keyword", "sequence", "running"]
    keys: list[KeyWord] = Field(default_factory=list, max_length=60)
    sequence: C.SequenceName | None = None
    source: PageName | None = None
    source_kind: Literal["plaintext", "ciphertext"] = "plaintext"
    offset_max: int = Field(0, ge=0, le=400)
    affine_mode: Literal["identity", "atbash", "shifts"] = "identity"
    interrupt_mode: Literal["none", "all"] = "none"

    @model_validator(mode="after")
    def _needs_key_material(self) -> SkipRuleH:
        need = {"keyword": self.keys, "sequence": self.sequence, "running": self.source}
        if not need[self.key_source]:
            field = {"keyword": "keys", "sequence": "sequence", "running": "source"}
            raise ValueError(f"key_source={self.key_source} requires {field[self.key_source]}")
        return self


Hypothesis = Annotated[
    AffineH | VigenereKeyH | VigenereClimbH | SequenceH | AutokeyH | RunningKeyH | SkipRuleH,
    Field(discriminator="family"),
]
_ADAPTER: TypeAdapter[Hypothesis] = TypeAdapter(Hypothesis)
FAMILIES = (
    "affine",
    "vigenere_key",
    "vigenere_climb",
    "sequence",
    "autokey",
    "running_key",
    "skip_rule",
)


def parse(data: dict[str, Any] | str) -> Hypothesis:
    """Validate untrusted JSON (dict or str) into a hypothesis; raises ValidationError."""
    if isinstance(data, str):
        return _ADAPTER.validate_json(data)
    return _ADAPTER.validate_python(data)


def json_schema() -> dict[str, Any]:
    return _ADAPTER.json_schema()


# --- execution ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    page: str
    family: str
    detail: str
    plaintext: IndexArray
    score: scoring.Score
    transform: Transform = "none"

    def preview(self, n: int = 120) -> str:
        return page_view(self.page, self.transform).render(self.plaintext)[:n]

    def as_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "family": self.family,
            "detail": self.detail,
            "quad": round(self.score.quad, 4),
            "words": round(self.score.words, 4),
            "combined": round(self.score.combined, 4),
            "preview": self.preview(),
        }


def page_view(name: str, transform: Transform = "none") -> corpus.Page:
    """The page as a given hypothesis sees it.

    ``delta``: c[i] - c[i-1] (undoes ciphertext-feedback autokey: c[i] = p[i] + k + c[i-1]);
    ``delta_sum``: c[i] + c[i-1]; ``reverse``: read the section back to front (layout too).
    """
    page = corpus.load(name)
    if transform == "none":
        return page
    if transform == "reverse":
        return corpus.Page.from_text(name, page.raw[::-1])
    c = page.runes.astype(np.int64)
    prev = np.concatenate([[0], c[:-1]])
    new = (c - prev) % N if transform == "delta" else (c + prev) % N
    return replace(page, runes=new.astype(np.uint8))


def affines(mode: AffineMode) -> list[C.Affine]:
    if mode == "identity":
        return [C.IDENTITY]
    if mode == "atbash":
        return [C.ATBASH]
    if mode == "shifts":
        return [C.Affine(a, b) for a in (1, N - 1) for b in range(N)]
    return [C.Affine(a, b) for a in range(1, N) for b in range(N)]


Decryptor = Callable[[C.BoolArray], IndexArray]

SKIP_PENALTY = 0.25


def _skip_options(ct: IndexArray, h: _Base) -> list[tuple[str, C.BoolArray]]:
    none = np.zeros(ct.size, dtype=np.bool_)
    if h.interrupter is None or h.interrupt_mode == "none":
        return [("no-int", none)]
    return [("no-int", none), (f"int={h.interrupter}:all", C.interrupter_mask(ct, h.interrupter))]


def refine_interrupters(
    ct: IndexArray,
    rune: int,
    decrypt: Decryptor,
    *,
    window: int = 48,
    max_joint: int = 4,
    max_occurrences: int = 400,
    skip_penalty: float = SKIP_PENALTY,
) -> tuple[C.BoolArray, float]:
    """Decide, left to right, which occurrences of ``rune`` are interrupters.

    At each occurrence, every on/off combination of it and the next occurrences inside a
    ``window``-rune lookahead (at most ``max_joint`` of them) is scored on that window; only
    the decision for the current occurrence is committed. Deciding clustered interrupters
    jointly avoids the misalignment trap of one-bit-at-a-time greedy search.

    Each skip costs ``skip_penalty`` (mean log10 units over the window). A real interrupter
    realigns the key and gains ~4 units, while a spurious one on wrong-key text gains ~0.1, so
    the penalty stops the search from "deleting its way" to better-looking gibberish.
    """
    quad = ngram.load().quad
    hits = np.flatnonzero(ct == rune)[:max_occurrences]
    skip = np.zeros(ct.size, dtype=np.bool_)
    for i, pos in enumerate(hits):
        group = [p for p in hits[i : i + max_joint] if p < pos + window]
        end = min(ct.size, pos + window)
        best_bits, best_score = 0, -np.inf
        for bits in range(1 << len(group)):
            trial = skip.copy()
            for b, p in enumerate(group):
                trial[p] = bool(bits >> b & 1)
            s = kernels.quad_score(decrypt(trial)[max(0, pos - 3) : end], quad)
            s -= skip_penalty * bin(bits).count("1")
            if s > best_score + 1e-9:
                best_bits, best_score = bits, s
        skip[pos] = bool(best_bits & 1)
    return skip, kernels.quad_score(decrypt(skip), quad)


def _finalise(
    page: corpus.Page,
    family: str,
    raw: Iterable[tuple[str, Decryptor, C.BoolArray]],
    h: _Base,
    top_k: int,
) -> list[Candidate]:
    """Score every (detail, decryptor, skip) option; refine interrupters on the best few."""
    quad = ngram.load().quad
    scored = sorted(
        ((kernels.quad_score(fn(skip), quad), d, fn, skip) for d, fn, skip in raw),
        key=lambda t: t[0],
        reverse=True,
    )
    bounds = page.word_bounds()
    out: list[Candidate] = []
    seen: set[str] = set()
    for _q, detail, fn, skip in scored[: max(top_k, 1) * 3]:
        if h.interrupt_mode == "greedy" and h.interrupter is not None:
            base = detail.rsplit("; ", 1)[0]  # drop the seed's skip label; refinement redoes it
            if base in seen:
                continue
            seen.add(base)
            refined, _ = refine_interrupters(page.runes, h.interrupter, fn)
            if scoring.quad_score(fn(refined)) >= scoring.quad_score(fn(skip)):
                skip = refined
            detail = f"{base}; int={h.interrupter}:greedy={int(skip.sum())}"
        pt = fn(skip)
        out.append(Candidate(page.name, family, detail, pt, scoring.score(pt, bounds), h.transform))
    out.sort(key=lambda c: c.score.combined, reverse=True)
    return out[:top_k]


def _desc(aff: C.Affine, sign: int) -> str:
    return f"a={aff.a},b={aff.b},sign={sign:+d}"


def execute(h: Hypothesis, top_k: int = 5) -> list[Candidate]:
    page = page_view(h.page, h.transform)
    ct = page.runes
    if isinstance(h, VigenereClimbH):
        return _execute_climb(h, page, top_k)
    if isinstance(h, SkipRuleH):
        return _execute_skip_rule(h, page, top_k)

    raw: list[tuple[str, Decryptor, C.BoolArray]] = []
    for aff in affines(h.affine_mode):
        for skip_name, skip0 in _skip_options(ct, h):
            for detail, fn in _decryptors(h, ct, aff):
                raw.append((f"{detail}; {_desc(aff, h.sign)}; {skip_name}", fn, skip0))
    return _finalise(page, h.family, raw, h, top_k)


def _decryptors(h: Hypothesis, ct: IndexArray, aff: C.Affine) -> list[tuple[str, Decryptor]]:
    s = h.sign
    if isinstance(h, AffineH):
        zeros = np.zeros_like(ct)
        return [("affine", lambda sk: C.decrypt_stream(ct, zeros, affine=aff, skip=sk))]
    if isinstance(h, VigenereKeyH):
        return [
            (f"key={k.upper()}", _vig(ct, k, s, aff)) for k in h.keys if latin_to_indices(k).size
        ]
    if isinstance(h, SequenceH):
        return [
            (f"seq={h.name}+{off}", _seq(ct, h.name, off, s, aff))
            for off in range(h.offset_max + 1)
        ]
    if isinstance(h, AutokeyH):
        return [
            (f"autokey={p.upper()}/{h.feedback}", _auto(ct, p, h.feedback, s, aff))
            for p in h.primers
            if latin_to_indices(p).size
        ]
    if isinstance(h, RunningKeyH):
        src_page = (
            corpus.load_solution(h.source)
            if h.source_kind == "plaintext" and h.source in corpus.SOLVED
            else corpus.load(h.source)
        )
        src = src_page.runes
        if src.size < ct.size:
            src = np.resize(src, ct.size + src.size)  # wrap short sources around
        return [
            (f"running={h.source}/{h.source_kind}@{off}", _run(ct, src, off, s, aff))
            for off in range(0, src.size - ct.size + 1)
        ]
    raise TypeError(f"unsupported hypothesis {type(h).__name__}")


# Closure factories (rather than lambdas in comprehensions) bind loop variables explicitly.
def _vig(ct: IndexArray, key: str, s: int, aff: C.Affine) -> Decryptor:
    return lambda sk: C.vigenere(ct, key, sign=s, affine=aff, skip=sk)


def _seq(ct: IndexArray, name: str, off: int, s: int, aff: C.Affine) -> Decryptor:
    def fn(sk: C.BoolArray) -> IndexArray:
        stream = C.sequence_stream(name, ct.size, offset=off, skip=sk)
        return C.decrypt_stream(ct, stream, sign=s, affine=aff, skip=sk)

    return fn


def _auto(ct: IndexArray, primer: str, feedback: str, s: int, aff: C.Affine) -> Decryptor:
    return lambda sk: C.autokey(ct, primer, sign=s, feedback=feedback, affine=aff, skip=sk)


def _run(ct: IndexArray, src: IndexArray, off: int, s: int, aff: C.Affine) -> Decryptor:
    return lambda sk: C.running_key(ct, src, offset=off, sign=s, affine=aff, skip=sk)


def _execute_climb(h: VigenereClimbH, page: corpus.Page, top_k: int) -> list[Candidate]:
    t = h.transform
    ct = page.runes
    quad = ngram.load().quad
    aff = C.ATBASH if h.affine_mode == "atbash" else C.IDENTITY
    bounds = page.word_bounds()
    out: list[Candidate] = []
    for skip_name, skip in _skip_options(ct, h):
        for period in range(h.period_min, h.period_max + 1):
            _q, key = kernels.climb_periodic(
                ct, period, quad, skip=skip, sign=h.sign, a=aff.a, b=aff.b,
                restarts=h.restarts, seed=period * 7919 + 1,
            )  # fmt: skip
            pt = C.vigenere(ct, key, sign=h.sign, affine=aff, skip=skip)
            detail = (
                f"period={period}; key={indices_to_latin(key)}; {_desc(aff, h.sign)}; {skip_name}"
            )
            out.append(Candidate(page.name, h.family, detail, pt, scoring.score(pt, bounds), t))
    out.sort(key=lambda c: c.score.combined, reverse=True)
    return out[:top_k]


def _key_materials(h: SkipRuleH, n: int) -> list[tuple[str, IndexArray]]:
    """(label, keystream of length >= 2n) for each key the hypothesis names."""
    need = 2 * n + 2
    if h.key_source == "keyword":
        return [
            (f"key={k.upper()}", np.resize(latin_to_indices(k), need))
            for k in h.keys
            if latin_to_indices(k).size
        ]
    if h.key_source == "sequence":
        assert h.sequence is not None
        return [
            (f"seq={h.sequence}+{off}", C.sequence(h.sequence, need, off))
            for off in range(h.offset_max + 1)
        ]
    assert h.source is not None
    src_page = (
        corpus.load_solution(h.source)
        if h.source_kind == "plaintext" and h.source in corpus.SOLVED
        else corpus.load(h.source)
    )
    src = np.resize(src_page.runes, src_page.runes.size + need)  # wrap around
    return [
        (f"running={h.source}/{h.source_kind}@{off}", src[off : off + need])
        for off in range(min(h.offset_max, src_page.runes.size) + 1)
    ]


def _execute_skip_rule(h: SkipRuleH, page: corpus.Page, top_k: int) -> list[Candidate]:
    from . import skiprule

    ct = page.runes
    bounds = page.word_bounds()
    out: list[Candidate] = []
    for skip_name, skip in _skip_options(ct, h):
        for label, key in _key_materials(h, ct.size):
            for aff in affines(h.affine_mode):
                pt, n_skips = skiprule.decode(ct, key, sign=h.sign, affine=aff, skip=skip)
                detail = f"{label}; {_desc(aff, h.sign)}; {skip_name}; key-skips={n_skips}"
                out.append(
                    Candidate(
                        page.name, h.family, detail, pt, scoring.score(pt, bounds), h.transform
                    )
                )
    out.sort(key=lambda c: c.score.combined, reverse=True)
    return out[:top_k]

"""Rune-space n-gram language model used to score candidate plaintexts.

Tables are log10 probabilities over 29 symbols, trained by ``scripts/build_ngrams.py`` from
public-domain English (transliterated with LP spelling rules) plus the solved LP plaintext.
Quadgram scoring is the fitness function for every search; it is implemented here in numpy
for clarity and in ``lplab.kernels`` (C / numba) for speed.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import numpy.typing as npt

from .gematria import IndexArray, N

NGRAM_PATH = Path(__file__).resolve().parents[2] / "data" / "ngrams.npz"

FloatArray = npt.NDArray[np.float32]


@dataclass(frozen=True)
class NgramModel:
    uni: FloatArray  # (29,)
    bi: FloatArray  # (29, 29)
    quad: FloatArray  # (29**4,) flat, index = ((a*29+b)*29+c)*29+d

    @property
    def unigram_probs(self) -> npt.NDArray[np.float64]:
        return np.power(10.0, self.uni.astype(np.float64))

    def quad_score(self, text: IndexArray) -> float:
        """Mean quadgram log10-probability per rune (higher = more English-like)."""
        if text.size < 4:
            return float("-inf")
        t = text.astype(np.int64)
        idx = ((t[:-3] * N + t[1:-2]) * N + t[2:-1]) * N + t[3:]
        return float(self.quad[idx].mean())

    def bigram_score(self, text: IndexArray) -> float:
        if text.size < 2:
            return float("-inf")
        t = text.astype(np.int64)
        return float(self.bi[t[:-1], t[1:]].mean())


def _log_probs(counts: npt.NDArray[np.float64], floor: float) -> FloatArray:
    total = counts.sum()
    probs = np.where(counts > 0, counts / total, floor / total)
    out: FloatArray = np.log10(probs).astype(np.float32)
    return out


def train(streams: list[IndexArray], floor: float = 0.01) -> NgramModel:
    """Count n-grams over each stream separately (no n-grams across stream boundaries)."""
    uni = np.zeros(N, dtype=np.float64)
    bi = np.zeros(N * N, dtype=np.float64)
    quad = np.zeros(N**4, dtype=np.float64)
    for s in streams:
        t = s.astype(np.int64)
        uni += np.bincount(t, minlength=N)
        if t.size >= 2:
            bi += np.bincount(t[:-1] * N + t[1:], minlength=N * N)
        if t.size >= 4:
            q = ((t[:-3] * N + t[1:-2]) * N + t[2:-1]) * N + t[3:]
            quad += np.bincount(q, minlength=N**4)
    return NgramModel(
        uni=_log_probs(uni, floor),
        bi=_log_probs(bi, floor).reshape(N, N),
        quad=_log_probs(quad, floor),
    )


def save(model: NgramModel, path: Path = NGRAM_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, uni=model.uni, bi=model.bi, quad=model.quad)


@cache
def load(path: Path = NGRAM_PATH) -> NgramModel:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing; run `python scripts/build_ngrams.py <corpus dir>` first"
        )
    with np.load(path) as z:
        return NgramModel(uni=z["uni"], bi=z["bi"], quad=z["quad"])

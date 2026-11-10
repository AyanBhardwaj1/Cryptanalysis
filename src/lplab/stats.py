"""Statistical fingerprints of rune streams.

The interesting LP anomaly lives here: the unsolved pages have far fewer *doublets*
(same rune twice in a row) than either random text (1/29) or English plaintext, which says
something about how the keystream was built (e.g. a key that never repeats a shift of 0 with
respect to the previous character). See ``doublet_rate`` and ``delta_histogram``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import numpy.typing as npt
from scipy import stats as sps

from .gematria import IndexArray, N

FloatVec = npt.NDArray[np.float64]


def counts(t: IndexArray) -> npt.NDArray[np.int64]:
    return np.bincount(t.astype(np.int64), minlength=N)


def ioc(t: IndexArray) -> float:
    """Index of coincidence, normalised so uniform random text ~ 1.0 (English runes ~ 1.7+)."""
    n = t.size
    if n < 2:
        return 0.0
    c = counts(t).astype(np.float64)
    return float((c * (c - 1)).sum() / (n * (n - 1)) * N)


def entropy(t: IndexArray) -> float:
    """Shannon entropy in bits per rune (max log2(29) ~ 4.858)."""
    if t.size == 0:
        return 0.0
    p = counts(t) / t.size
    return float(sps.entropy(p[p > 0], base=2))


def doublet_rate(t: IndexArray) -> float:
    """Fraction of adjacent pairs with the same rune. Random text: 1/29 ~ 0.0345."""
    if t.size < 2:
        return 0.0
    return float(np.mean(t[1:] == t[:-1]))


def delta_histogram(t: IndexArray) -> npt.NDArray[np.int64]:
    """Histogram of (t[i+1] - t[i]) mod 29. A hole at 0 is the doublet anomaly."""
    d = (t[1:].astype(np.int64) - t[:-1].astype(np.int64)) % N
    return np.bincount(d, minlength=N)


def periodic_ioc(t: IndexArray, max_period: int = 40) -> FloatVec:
    """Mean IoC of the ``p`` interleaved columns for p = 1..max_period (index 0 unused).

    A periodic polyalphabetic key of length L shows peaks at L and its multiples.
    """
    out = np.zeros(max_period + 1)
    for p in range(1, max_period + 1):
        cols = [t[i::p] for i in range(p)]
        out[p] = float(np.mean([ioc(c) for c in cols if c.size > 1]))
    return out


def chi2_vs(t: IndexArray, expected_probs: FloatVec) -> tuple[float, float]:
    """Chi-squared statistic and p-value of rune counts against an expected distribution."""
    obs = counts(t).astype(np.float64)
    exp = expected_probs / expected_probs.sum() * obs.sum()
    res = sps.chisquare(obs, exp)
    return float(res.statistic), float(res.pvalue)


def doublet_pvalue(t: IndexArray) -> float:
    """Binomial p-value of seeing this few doublets if adjacent runes were independent uniform."""
    if t.size < 2:
        return 1.0
    k = int(np.sum(t[1:] == t[:-1]))
    return float(sps.binom.cdf(k, t.size - 1, 1 / N))


@dataclass(frozen=True)
class Fingerprint:
    length: int
    ioc: float
    entropy: float
    doublet_rate: float
    doublet_pvalue: float
    best_period: int
    best_period_ioc: float

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def fingerprint(t: IndexArray, max_period: int = 40) -> Fingerprint:
    per = periodic_ioc(t, min(max_period, max(1, t.size // 8)))
    best = int(np.argmax(per[1:]) + 1) if per.size > 1 else 1
    return Fingerprint(
        length=int(t.size),
        ioc=ioc(t),
        entropy=entropy(t),
        doublet_rate=doublet_rate(t),
        doublet_pvalue=doublet_pvalue(t),
        best_period=best,
        best_period_ioc=float(per[best]),
    )

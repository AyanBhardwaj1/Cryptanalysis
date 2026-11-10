"""Mechanism screening: which cipher families can reproduce the unsolved pages' statistics?

Brute-forcing a family is expensive; ruling it out statistically is cheap. Each mechanism here
encrypts real LP-English plaintext with random key material, and :func:`screen` compares the
resulting fingerprint (IoC, doublet rate) with the unsolved pages. A family whose doublet rate
can't get near the observed ~0.66% (vs 3.45% for random text) needs an extra rule to be viable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt
from scipy import stats as sps

from . import corpus, stats
from .ciphers import sequence
from .gematria import IndexArray, N

Rng = np.random.Generator
Mechanism = Callable[[IndexArray, Rng], IndexArray]


def _english(rng: Rng, n: int) -> IndexArray:
    """n runes of LP English: a random window of the concatenated solved plaintext."""
    text = np.concatenate([corpus.load_solution(s).runes for s in corpus.SOLVED])
    start = int(rng.integers(0, max(1, text.size - n)))
    return text[start : start + n].copy()


def _add(p: IndexArray, k: npt.NDArray[np.integer[Any]]) -> IndexArray:
    return ((p.astype(np.int64) + k) % N).astype(np.uint8)


def vigenere(period: int) -> Mechanism:
    return lambda p, rng: _add(p, np.resize(rng.integers(0, N, period), p.size))


def one_time_pad(p: IndexArray, rng: Rng) -> IndexArray:
    return _add(p, rng.integers(0, N, p.size))


def running_key(p: IndexArray, rng: Rng) -> IndexArray:
    return _add(p, _english(rng, p.size))


def prime_stream(p: IndexArray, rng: Rng) -> IndexArray:
    off = int(rng.integers(0, 200))
    return _add(p, sequence("totient_primes", p.size, off))


def autokey_plain(p: IndexArray, rng: Rng) -> IndexArray:
    primer = rng.integers(0, N, 8)
    return _add(p, np.concatenate([primer, p[:-8]]) if p.size > 8 else primer[: p.size])


def autokey_cipher(p: IndexArray, rng: Rng) -> IndexArray:
    c = np.empty_like(p)
    prev = int(rng.integers(0, N))
    for i, x in enumerate(p.tolist()):
        prev = (x + prev) % N
        c[i] = prev
    return c


def otp_no_doublets(p: IndexArray, rng: Rng) -> IndexArray:
    """Random key, redrawn whenever it would produce c[i] == c[i-1]."""
    c = np.empty_like(p)
    for i, x in enumerate(p.tolist()):
        while True:
            v = (x + int(rng.integers(0, N))) % N
            if i == 0 or v != c[i - 1]:
                break
        c[i] = v
    return c


def plain_minus_previous_cipher(p: IndexArray, rng: Rng) -> IndexArray:
    """c[i] = p[i] + c[i-1] + k[i] with a random k that is never 0 mod 29 (no doublets when p=0)."""
    k = rng.integers(1, N, p.size)
    c = np.empty_like(p)
    prev = int(rng.integers(0, N))
    for i, x in enumerate(p.tolist()):
        prev = (x + prev + int(k[i])) % N
        c[i] = prev
    return c


def skip_if_same(q: float, running: bool = False) -> Mechanism:
    """Keystream + skip-if-same rule firing with probability q (lplab.skiprule)."""
    from . import skiprule

    def mech(p: IndexArray, rng: Rng) -> IndexArray:
        key = (
            _english(rng, 2 * p.size + 2)
            if running
            else np.resize(rng.integers(0, N, 8), 2 * p.size + 2)
        )
        return skiprule.encrypt(p, key.astype(np.uint8), q=q, rng=rng)

    return mech


MECHANISMS: dict[str, Mechanism] = {
    "vigenere_p8": vigenere(8),
    "vigenere_p29": vigenere(29),
    "one_time_pad": one_time_pad,
    "running_key_english": running_key,
    "totient_prime_stream": prime_stream,
    "autokey_plaintext": autokey_plain,
    "autokey_ciphertext": autokey_cipher,
    "otp_no_doublets": otp_no_doublets,
    "cipher_feedback_nonzero_key": plain_minus_previous_cipher,
    "vigenere_p8_skip_if_same_q1": skip_if_same(1.0),
    "vigenere_p8_skip_if_same_q081": skip_if_same(0.81),
    "running_key_skip_if_same_q081": skip_if_same(0.81, running=True),
}


@dataclass(frozen=True)
class ScreenRow:
    mechanism: str
    ioc: float
    doublet_rate: float
    doublet_sd: float
    matches_observed: bool


def observed() -> stats.Fingerprint:
    return stats.fingerprint(corpus.all_unsolved_runes())


def doublet_fit_pvalue(mechanism_rate: float, obs: stats.Fingerprint) -> float:
    """Two-sided binomial p-value of the observed doublet count if the true rate were this one."""
    n = obs.length - 1
    k = round(obs.doublet_rate * n)
    return float(sps.binomtest(k, n, min(max(mechanism_rate, 1e-9), 1.0)).pvalue)


def screen(trials: int = 30, length: int = 1500, seed: int = 3301) -> list[ScreenRow]:
    """Fingerprint each mechanism on LP English with random keys.

    ``matches_observed``: the observed doublet count over all unsolved pages is plausible
    (binomial p > 1e-3) under the mechanism's mean doublet rate. IoC is reported, not tested:
    every family here is already flat (~1.0) like the pages.
    """
    rng = np.random.default_rng(seed)
    obs = observed()
    rows = []
    for name, mech in MECHANISMS.items():
        iocs, dbl = [], []
        for _ in range(trials):
            c = mech(_english(rng, length), rng)
            iocs.append(stats.ioc(c))
            dbl.append(stats.doublet_rate(c))
        d_mean, d_sd = float(np.mean(dbl)), float(np.std(dbl))
        ok = doublet_fit_pvalue(d_mean, obs) > 1e-3
        rows.append(ScreenRow(name, float(np.mean(iocs)), d_mean, d_sd, ok))
    return rows

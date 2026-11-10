"""Decryptors over rune indices (mod 29).

Every cipher solved so far in the Liber Primus fits one shape::

    x_i = (c_i - sign * k_j) mod 29        # keystream step (j advances only on non-skipped runes)
    p_i = (a * x_i + b) mod 29             # affine step: identity, shift, atbash, atbash+shift

with "interrupter" positions (a chosen rune, usually ᚠ) passed through unchanged and not
consuming key. ``atbash`` is ``a=28 (=-1), b=28``; the koan page is ``a=-1, b=2``; the
"Welcome" page is Vigenère ``DIVINITY``; "An End" is the stream ``phi(prime_j)``.

All functions return new arrays and never mutate their inputs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import Literal, get_args

import numpy as np
import numpy.typing as npt
from numba import njit

from .gematria import IndexArray, N, latin_to_indices

BoolArray = npt.NDArray[np.bool_]


@dataclass(frozen=True)
class Affine:
    """p = a*x + b (mod 29). ``a`` must be non-zero (29 is prime, so every a != 0 inverts)."""

    a: int = 1
    b: int = 0

    def __post_init__(self) -> None:
        if not 1 <= self.a % N <= N - 1:
            raise ValueError("affine multiplier must be non-zero mod 29")

    def apply(self, x: IndexArray) -> IndexArray:
        return ((self.a * x.astype(np.int64) + self.b) % N).astype(np.uint8)

    def inverse(self) -> Affine:
        inv = pow(self.a % N, -1, N)
        return Affine(inv, (-inv * self.b) % N)


IDENTITY = Affine(1, 0)
ATBASH = Affine(N - 1, N - 1)


def interrupter_mask(
    ct: IndexArray, rune: int | None, skip_occurrences: Sequence[int] | None = None
) -> BoolArray:
    """Boolean mask of positions treated as interrupters.

    ``rune=None`` means no interrupters. ``skip_occurrences=None`` means every occurrence of
    ``rune`` is an interrupter; otherwise only the listed 0-based occurrence numbers are.
    """
    mask = np.zeros(ct.size, dtype=np.bool_)
    if rune is None:
        return mask
    hits = np.flatnonzero(ct == rune)
    if skip_occurrences is None:
        mask[hits] = True
    else:
        chosen = [hits[i] for i in skip_occurrences if 0 <= i < hits.size]
        mask[chosen] = True
    return mask


def expand_keystream(key: IndexArray, n: int, skip: BoolArray | None = None) -> IndexArray:
    """Repeat/align ``key`` over ``n`` positions; skipped positions get key 0 and don't advance."""
    if key.size == 0:
        raise ValueError("empty key")
    if skip is None or not skip.any():
        return np.resize(key, n).astype(np.uint8)
    out = np.zeros(n, dtype=np.uint8)
    live = np.flatnonzero(~skip)
    out[live] = np.resize(key, live.size)
    return out


def decrypt_stream(
    ct: IndexArray,
    stream: IndexArray,
    *,
    sign: int = 1,
    affine: Affine = IDENTITY,
    skip: BoolArray | None = None,
) -> IndexArray:
    """Core decryptor. ``stream`` is the already-aligned per-position keystream (length n)."""
    if stream.size != ct.size:
        raise ValueError("stream must be aligned to the ciphertext")
    x = (ct.astype(np.int64) - sign * stream.astype(np.int64)) % N
    p = affine.apply(x.astype(np.uint8))
    if skip is not None and skip.any():
        p = p.copy()
        p[skip] = ct[skip]
    return p


def encrypt_stream(
    pt: IndexArray,
    stream: IndexArray,
    *,
    sign: int = 1,
    affine: Affine = IDENTITY,
    skip: BoolArray | None = None,
) -> IndexArray:
    """Exact inverse of :func:`decrypt_stream` (for round-trip tests and synthetic benchmarks)."""
    x = affine.inverse().apply(pt)
    c = ((x.astype(np.int64) + sign * stream.astype(np.int64)) % N).astype(np.uint8)
    if skip is not None and skip.any():
        c[skip] = pt[skip]
    return c


def vigenere(
    ct: IndexArray,
    key: IndexArray | str,
    *,
    sign: int = 1,
    affine: Affine = IDENTITY,
    skip: BoolArray | None = None,
) -> IndexArray:
    k = latin_to_indices(key) if isinstance(key, str) else key
    return decrypt_stream(
        ct, expand_keystream(k, ct.size, skip), sign=sign, affine=affine, skip=skip
    )


# --- number-theoretic keystreams ---------------------------------------------------------


@cache
def _primes(count: int) -> tuple[int, ...]:
    limit = max(32, int(count * (np.log(count + 2) + np.log(np.log(count + 3)) + 3)))
    while True:
        sieve = np.ones(limit + 1, dtype=np.bool_)
        sieve[:2] = False
        for i in range(2, int(limit**0.5) + 1):
            if sieve[i]:
                sieve[i * i :: i] = False
        ps = np.flatnonzero(sieve)
        if ps.size >= count:
            return tuple(int(p) for p in ps[:count])
        limit *= 2


def primes(count: int) -> npt.NDArray[np.int64]:
    return np.asarray(_primes(count), dtype=np.int64)


def _fibonacci(count: int) -> npt.NDArray[np.int64]:
    out = np.zeros(count, dtype=np.int64)
    a, b = 0, 1
    for i in range(count):
        out[i] = a
        a, b = b, (a + b) % N
    return out


def _totient_table(limit: int) -> npt.NDArray[np.int64]:
    phi = np.arange(limit + 1, dtype=np.int64)
    for i in range(2, limit + 1):
        if phi[i] == i:
            phi[i::i] -= phi[i::i] // i
    return phi


SequenceName = Literal[
    "primes",
    "totient_primes",
    "naturals",
    "totient_naturals",
    "fibonacci",
    "squares",
    "triangular",
]
SEQUENCES: tuple[str, ...] = get_args(SequenceName)


def sequence(name: str, count: int, offset: int = 0) -> IndexArray:
    """A named integer sequence (starting at element ``offset``) reduced mod 29."""
    if name not in SEQUENCES:
        raise ValueError(f"unknown sequence {name!r}; known: {SEQUENCES}")
    total = count + offset
    if name == "primes":
        seq = primes(total)
    elif name == "totient_primes":
        seq = primes(total) - 1
    elif name == "naturals":
        seq = np.arange(total, dtype=np.int64)
    elif name == "totient_naturals":
        seq = _totient_table(max(total, 1))[:total]
    elif name == "fibonacci":
        seq = _fibonacci(total)
    elif name == "squares":
        seq = np.arange(total, dtype=np.int64) ** 2
    else:
        r = np.arange(total, dtype=np.int64)
        seq = r * (r + 1) // 2
    return (seq[offset:] % N).astype(np.uint8)


def sequence_stream(
    name: str, n: int, *, offset: int = 0, skip: BoolArray | None = None
) -> IndexArray:
    live = n if skip is None else int((~skip).sum())
    return expand_keystream(sequence(name, max(live, 1), offset), n, skip)


# --- autokey (sequential, so compiled) ---------------------------------------------------


@njit(cache=True)  # type: ignore[misc,unused-ignore]
def _autokey_kernel(
    ct: IndexArray,
    primer: IndexArray,
    sign: int,
    feedback_plain: bool,
    skip: BoolArray,
    a: int,
    b: int,
) -> IndexArray:  # pragma: no cover - compiled; covered via autokey()
    n = ct.size
    m = primer.size
    out = np.empty(n, dtype=np.uint8)
    hist = np.empty(n + m, dtype=np.int64)
    for i in range(m):
        hist[i] = primer[i]
    j = 0
    for i in range(n):
        if skip[i]:
            out[i] = ct[i]
            continue
        k = hist[j]
        x = (int(ct[i]) - sign * k) % 29
        p = (a * x + b) % 29  # the true plaintext is what feeds back, after the affine step
        out[i] = p
        hist[j + m] = p if feedback_plain else ct[i]
        j += 1
    return out


def autokey(
    ct: IndexArray,
    primer: IndexArray | str,
    *,
    sign: int = 1,
    feedback: str = "plain",
    affine: Affine = IDENTITY,
    skip: BoolArray | None = None,
) -> IndexArray:
    """Autokey: key = primer followed by the plaintext (or ciphertext) itself."""
    if feedback not in ("plain", "cipher"):
        raise ValueError("feedback must be 'plain' or 'cipher'")
    k = latin_to_indices(primer) if isinstance(primer, str) else primer
    if k.size == 0:
        raise ValueError("empty primer")
    s = np.zeros(ct.size, dtype=np.bool_) if skip is None else skip
    p: IndexArray = _autokey_kernel(
        ct, k.astype(np.uint8), sign, feedback == "plain", s, affine.a % N, affine.b % N
    )
    return p


def running_key(
    ct: IndexArray,
    source: IndexArray,
    *,
    offset: int = 0,
    sign: int = 1,
    affine: Affine = IDENTITY,
    skip: BoolArray | None = None,
) -> IndexArray:
    """Running-key cipher: the key is a long text (e.g. another LP section) from ``offset``."""
    live = ct.size if skip is None else int((~skip).sum())
    if offset < 0 or offset + live > source.size:
        raise ValueError("source text too short for this offset")
    stream = expand_keystream(source[offset : offset + live], ct.size, skip)
    return decrypt_stream(ct, stream, sign=sign, affine=affine, skip=skip)

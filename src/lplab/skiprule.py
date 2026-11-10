"""Keystream ciphers with a *skip-if-same* rule: the leading explanation of the doublet deficit.

Encryption (sign s, keystream K, rule fires with probability q)::

    c = x_i + s*K[j]                 # x_i = affine^-1(p_i)
    if c == c[i-1] and rule fires:   # would repeat the previous ciphertext rune
        j += 1; c = x_i + s*K[j]     # burn a key element and re-encrypt
    j += 1

With q ~ 0.81 this turns English (3%+ doublets under any independent key) into ciphertext
with ~0.66% doublets, as observed on the unsolved pages, while keeping IoC flat.

Decryption is ambiguous only where a skip *could* have happened: position i with key pointer
j is a branch point iff ``(c_i - s*K[j+1]) + s*K[j] == c_{i-1}`` (about 1 position in 29).
:func:`decode` walks left to right and resolves each branch point by which choice reads better
over a lookahead window under the quadgram model, the same strategy that finds interrupters.
"""

from __future__ import annotations

import numpy as np
from numba import njit

from . import kernels, ngram
from .ciphers import IDENTITY, Affine, BoolArray
from .gematria import IndexArray, N

UNDECIDED, NO_SKIP, SKIP = -1, 0, 1


def encrypt(
    pt: IndexArray,
    key: IndexArray,
    *,
    sign: int = 1,
    affine: Affine = IDENTITY,
    q: float = 1.0,
    rng: np.random.Generator | None = None,
    skip: BoolArray | None = None,
) -> IndexArray:
    """Reference encryptor (positive controls, simulation). ``key`` must be long enough."""
    rng = rng or np.random.default_rng(0)
    x = affine.inverse().apply(pt).astype(np.int64)
    out = np.empty(pt.size, dtype=np.uint8)
    j = 0
    prev = -1
    for i in range(pt.size):
        if skip is not None and skip[i]:
            out[i] = pt[i]
            prev = int(pt[i])
            continue
        c = (int(x[i]) + sign * int(key[j])) % N
        if c == prev and rng.random() < q:
            j += 1
            c = (int(x[i]) + sign * int(key[j])) % N
        out[i] = c
        prev = c
        j += 1
    return out


@njit(cache=True)  # type: ignore[misc,unused-ignore]
def _decode_kernel(
    ct: np.ndarray, key: np.ndarray, sign: int, decisions: np.ndarray, skip: BoolArray
) -> tuple[IndexArray, np.ndarray]:  # pragma: no cover - compiled; covered via decode()
    """Decode under fixed decisions; return pre-affine x and a branch-point mask.

    decisions[i] in {UNDECIDED, NO_SKIP, SKIP}; UNDECIDED branch points default to NO_SKIP.
    """
    n = ct.size
    x = np.empty(n, dtype=np.uint8)
    branch = np.zeros(n, dtype=np.bool_)
    j = 0
    for i in range(n):
        if skip[i]:
            x[i] = ct[i]
            continue
        if j + 1 >= key.size:
            x[i] = (ct[i] - sign * key[j % key.size]) % 29
            j += 1
            continue
        if i > 0:
            alt = (ct[i] - sign * key[j + 1]) % 29
            if (alt + sign * key[j]) % 29 == ct[i - 1]:
                branch[i] = True
                if decisions[i] == 1:
                    x[i] = alt
                    j += 2
                    continue
        x[i] = (ct[i] - sign * key[j]) % 29
        j += 1
    return x, branch


def decode(
    ct: IndexArray,
    key: IndexArray,
    *,
    sign: int = 1,
    affine: Affine = IDENTITY,
    skip: BoolArray | None = None,
    window: int = 40,
    depth: int = 4,
    skip_penalty: float = 0.0,
) -> tuple[IndexArray, int]:
    """LM-guided decode. Returns (plaintext, number of key skips chosen).

    ``skip_penalty`` (mean log10 units) can be charged per chosen skip, as for interrupters.
    It defaults to 0: measured, it barely reduces spurious skips on wrong keys (9 -> 8 on p0-2)
    but costs exact recovery on short periodic keys, where a misaligned key still partly fits.
    """
    quad = ngram.load().quad
    sk = np.zeros(ct.size, dtype=np.bool_) if skip is None else skip
    k = np.ascontiguousarray(key, dtype=np.int64)
    c = np.ascontiguousarray(ct, dtype=np.int64)
    decisions = np.full(ct.size, UNDECIDED, dtype=np.int64)

    def run() -> tuple[IndexArray, np.ndarray]:
        x, branch = _decode_kernel(c, k, sign, decisions, sk)
        return affine.apply(x), branch

    def lookahead(lo: int, hi: int, after: int, depth: int) -> float:
        """Best window score over the next ``depth`` open branch points inside the window."""
        trial, branch = run()
        nxt = np.flatnonzero(branch[after:hi] & (decisions[after:hi] == UNDECIDED))
        if depth == 0 or nxt.size == 0:
            return kernels.quad_score(trial[lo:hi], quad)
        b = after + int(nxt[0])
        best = -np.inf
        for choice in (NO_SKIP, SKIP):
            decisions[b] = choice
            best = max(best, lookahead(lo, hi, b + 1, depth - 1))
        decisions[b] = UNDECIDED
        return best

    pt, branch = run()
    pos = 0
    while True:
        open_points = np.flatnonzero(branch[pos:] & (decisions[pos:] == UNDECIDED))
        if open_points.size == 0:
            break
        i = pos + int(open_points[0])
        lo, hi = max(0, i - 3), min(ct.size, i + window)
        scores = {}
        for choice in (NO_SKIP, SKIP):
            decisions[i] = choice
            scores[choice] = lookahead(lo, hi, i + 1, depth)
        decisions[i] = SKIP if scores[SKIP] - skip_penalty > scores[NO_SKIP] else NO_SKIP
        pt, branch = run()
        pos = i + 1
    final = pt.copy()
    if skip is not None:
        final[skip] = ct[skip]
    return final, int((decisions == SKIP).sum())

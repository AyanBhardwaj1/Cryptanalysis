"""Known-plaintext helpers: recover keystreams and interrupter positions from (ct, pt) pairs.

Used to turn the solved LP sections into exact regression fixtures, and as a crib tool:
give it a guessed plaintext fragment and it tells you what keystream would produce it.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .ciphers import IDENTITY, Affine, BoolArray
from .gematria import IndexArray, N


def keystream_from_pair(
    ct: IndexArray, pt: IndexArray, *, sign: int = 1, affine: Affine = IDENTITY
) -> IndexArray:
    """k such that decrypt(ct, k) == pt, position by position (no interrupters)."""
    if ct.size != pt.size:
        raise ValueError("ciphertext and plaintext lengths differ")
    x = affine.inverse().apply(pt).astype(np.int64)
    return (((ct.astype(np.int64) - x) * sign) % N).astype(np.uint8)


def fit_interrupters(
    ct: IndexArray,
    pt: IndexArray,
    key_at: Callable[[int], int],
    *,
    rune: int = 0,
    sign: int = 1,
    affine: Affine = IDENTITY,
    lookahead: int = 24,
) -> tuple[BoolArray, int]:
    """Greedy alignment of a keystream ``key_at(j)`` against known plaintext.

    At every occurrence of ``rune`` whose plaintext equals the ciphertext, decide whether it is
    an interrupter (key does not advance) by checking which choice keeps the next
    ``lookahead`` positions consistent. Returns the skip mask and the number of mismatches.
    """
    inv = affine.inverse()

    def fits(i: int, j: int) -> bool:
        x = int(inv.apply(np.array([pt[i]], dtype=np.uint8))[0])
        return (int(ct[i]) - sign * key_at(j)) % N == x

    def score(i: int, j: int) -> int:
        # lazy policy inside the window: skip a candidate only when the key doesn't fit it
        ok = 0
        for t in range(i, min(i + lookahead, ct.size)):
            if fits(t, j):
                ok += 1
                j += 1
            elif ct[t] == rune and pt[t] == ct[t]:
                ok += 1
            else:
                j += 1
        return ok

    skip = np.zeros(ct.size, dtype=np.bool_)
    mismatches = 0
    j = 0
    for i in range(ct.size):
        candidate = ct[i] == rune and pt[i] == ct[i]
        # skipping matches position i for free; not skipping must match it with key j
        if candidate and 1 + score(i + 1, j) > int(fits(i, j)) + score(i + 1, j + 1):
            skip[i] = True
            continue
        if not fits(i, j):
            mismatches += 1
        j += 1
    return skip, mismatches

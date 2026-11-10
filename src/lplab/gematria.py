"""Gematria Primus: the 29-rune alphabet used by the Liber Primus.

Every rune has an index (0..28, futhorc order), one or more Latin readings, and a prime value.
All cipher code in this package works on ``uint8`` index arrays; this module converts between
runes, indices, primes and Latin text.
"""

from __future__ import annotations

from typing import Final

import numpy as np
import numpy.typing as npt

N: Final = 29

# (rune, canonical latin, alternative latin readings, prime)
_TABLE: Final = (
    ("ᚠ", "F", (), 2),
    ("ᚢ", "U", ("V",), 3),
    ("ᚦ", "TH", (), 5),
    ("ᚩ", "O", (), 7),
    ("ᚱ", "R", (), 11),
    ("ᚳ", "C", ("K",), 13),
    ("ᚷ", "G", (), 17),
    ("ᚹ", "W", (), 19),
    ("ᚻ", "H", (), 23),
    ("ᚾ", "N", (), 29),
    ("ᛁ", "I", (), 31),
    ("ᛄ", "J", (), 37),
    ("ᛇ", "EO", (), 41),
    ("ᛈ", "P", (), 43),
    ("ᛉ", "X", (), 47),
    ("ᛋ", "S", ("Z",), 53),
    ("ᛏ", "T", (), 59),
    ("ᛒ", "B", (), 61),
    ("ᛖ", "E", (), 67),
    ("ᛗ", "M", (), 71),
    ("ᛚ", "L", (), 73),
    ("ᛝ", "NG", ("ING",), 79),
    ("ᛟ", "OE", (), 83),
    ("ᛞ", "D", (), 89),
    ("ᚪ", "A", (), 97),
    ("ᚫ", "AE", (), 101),
    ("ᚣ", "Y", (), 103),
    ("ᛡ", "IA", ("IO",), 107),
    ("ᛠ", "EA", (), 109),
)

RUNES: Final[tuple[str, ...]] = tuple(row[0] for row in _TABLE)
LATIN: Final[tuple[str, ...]] = tuple(row[1] for row in _TABLE)
PRIMES: Final[tuple[int, ...]] = tuple(row[3] for row in _TABLE)
RUNE_TO_INDEX: Final[dict[str, int]] = {r: i for i, r in enumerate(RUNES)}

# Latin -> index, longest readings first so greedy matching picks digraphs/trigraphs.
_LATIN_TO_INDEX: dict[str, int] = {}
for _i, (_r, _lat, _alts, _p) in enumerate(_TABLE):
    _LATIN_TO_INDEX[_lat] = _i
    for _alt in _alts:
        _LATIN_TO_INDEX[_alt] = _i
_LATIN_TO_INDEX["Q"] = _LATIN_TO_INDEX["C"]  # Q is written CW in the LP; handled below
_LATIN_KEYS: Final = sorted(_LATIN_TO_INDEX, key=len, reverse=True)

IndexArray = npt.NDArray[np.uint8]


def is_rune(ch: str) -> bool:
    return ch in RUNE_TO_INDEX


def runes_to_indices(text: str) -> IndexArray:
    """Indices of every rune in ``text``; non-rune characters are dropped."""
    return np.fromiter((RUNE_TO_INDEX[c] for c in text if c in RUNE_TO_INDEX), dtype=np.uint8)


def indices_to_runes(idx: npt.ArrayLike) -> str:
    return "".join(RUNES[int(i)] for i in np.asarray(idx).ravel())


def indices_to_latin(idx: npt.ArrayLike) -> str:
    return "".join(LATIN[int(i)] for i in np.asarray(idx).ravel())


def latin_to_indices(text: str) -> IndexArray:
    """Greedy transliteration of English into rune indices.

    Letters outside the alphabet (digits, punctuation, spaces) are dropped. ``Q`` becomes
    ``CW`` and ``ING``/``NG`` become the single rune ``ᛝ``, matching LP spelling.
    """
    up = "".join(ch for ch in text.upper() if "A" <= ch <= "Z")
    out: list[int] = []
    i = 0
    while i < len(up):
        if up[i] == "Q":
            out.extend((_LATIN_TO_INDEX["C"], _LATIN_TO_INDEX["W"]))
            i += 2 if up[i : i + 2] == "QU" else 1
            continue
        for key in _LATIN_KEYS:
            if up.startswith(key, i):
                out.append(_LATIN_TO_INDEX[key])
                i += len(key)
                break
        else:  # pragma: no cover - every A..Z letter has a reading
            raise ValueError(f"no rune for {up[i]!r}")
    return np.asarray(out, dtype=np.uint8)


def primes_of(idx: npt.ArrayLike) -> npt.NDArray[np.int64]:
    return np.asarray(PRIMES, dtype=np.int64)[np.asarray(idx, dtype=np.intp)]


def gematria_sum(idx: npt.ArrayLike) -> int:
    """Sum of prime values, the 'gematria sum' Cicada uses for words and lines."""
    return int(primes_of(idx).sum())

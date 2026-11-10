"""Seed key material: words from the solved LP pages and recurring Cicada 3301 themes.

The heuristic planner draws keys and primers from here; the Haiku keyword worker extends it.
"""

from __future__ import annotations

import re
from functools import cache

from . import corpus
from .gematria import indices_to_latin, runes_to_indices

CURATED = (
    "DIVINITY", "CIRCUMFERENCE", "FIRFUMFERENFE", "PRIMES", "TOTIENT", "INSTAR", "EMERGENCE",
    "CICADA", "LIBERPRIMUS", "PRIMUS", "LIBER", "PARABLE", "KOAN", "WISDOM", "SACRED",
    "ENLIGHTENMENT", "CONSUMPTION", "PRESERVATION", "ADHERENCE", "SHED", "TUNNELING",
    "SURFACE", "PILGRIM", "JOURNEY", "INSTRUCTION", "MASTER", "VOICE", "TRUTH", "KNOWLEDGE",
    "EXPERIENCE", "DEATH", "BEING", "CONSCIOUSNESS", "ILLUSION", "REALITY", "SELF", "MOBIUS",
    "THREE", "THIRTYONE", "SEVENTEEN", "ELEVEN", "PRIME", "SPIRAL", "WELCOME", "WARNING",
    "AN END", "QUESTION", "FIND THE DIVINITY WITHIN", "DEEP WEB", "ONION", "LOSS",
    "THE PRIMES ARE SACRED", "THE TOTIENT FUNCTION IS SACRED", "ALL THINGS SHOULD BE ENCRYPTED",
    "CONSUME", "PRESERVE", "ADHERE", "EMERGE", "AMASS", "MASTERY", "SHADOWS", "GOD", "LIGHT",
)  # fmt: skip


@cache
def solved_words(min_len: int = 5) -> tuple[str, ...]:
    """Distinct words (Latin transliteration) from the solved LP plaintext."""
    seen: dict[str, None] = {}
    for name in corpus.SOLVED:
        raw = corpus.load_solution(name).raw
        for w in re.split(r"[^ᚠ-᛿]+", raw):
            if len(w) >= min_len:
                seen.setdefault(indices_to_latin(runes_to_indices(w)), None)
    return tuple(seen)


def seed_keys() -> tuple[str, ...]:
    out: dict[str, None] = dict.fromkeys(CURATED)
    for w in solved_words():
        out.setdefault(w, None)
    return tuple(out)

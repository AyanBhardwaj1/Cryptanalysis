"""Candidate scoring: quadgram fitness plus word-level dictionary hits.

The LP preserves word boundaries, so a correct decryption must split into real words at the
original separators. ``word_score`` exploits that and is a much sharper filter than n-grams
alone; ``is_promising`` combines both into the cheap gate that decides which candidates are
worth an LLM judge call.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np

from . import kernels, ngram
from .gematria import RUNE_TO_INDEX, IndexArray, indices_to_runes

VOCAB_PATH = ngram.NGRAM_PATH.with_name("vocab.txt.gz")

# Calibrated on the solved pages (English ~ -4.2, random ~ -8.4; see tests/test_scoring.py).
QUAD_PROMISING = -6.0
WORDS_PROMISING = 0.45


@cache
def vocab(path: Path = VOCAB_PATH) -> frozenset[str]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return frozenset(line.split("\t", 1)[0] for line in fh if line.strip())


def quad_score(text: IndexArray) -> float:
    return kernels.quad_score(text, ngram.load().quad)


# Every one-rune word in the solved LP plaintext is A or I (27 of 27, ignoring contractions).
ONE_RUNE_WORDS = frozenset({RUNE_TO_INDEX["ᚪ"], RUNE_TO_INDEX["ᛁ"]})


def word_score(text: IndexArray, bounds: list[tuple[int, int]]) -> float:
    """Length-weighted fraction of words that are real: dictionary words for 2+ runes, and
    A or I for one-rune words (a strong, nearly free constraint: random text passes 2/29)."""
    words = vocab()
    hit = total = 0
    for start, end in bounds:
        n = end - start
        total += n
        if n == 1:
            hit += int(text[start]) in ONE_RUNE_WORDS
        elif indices_to_runes(text[start:end]) in words:
            hit += n
    return hit / total if total else 0.0


@dataclass(frozen=True)
class Score:
    quad: float
    words: float

    @property
    def combined(self) -> float:
        # map quad from [-8.5 (random), -4 (English)] to ~[0, 1] and average with word hits
        q = float(np.clip((self.quad + 8.5) / 4.5, 0.0, 1.2))
        return 0.5 * q + 0.5 * self.words

    @property
    def promising(self) -> bool:
        return self.quad > QUAD_PROMISING or self.words > WORDS_PROMISING


def score(text: IndexArray, bounds: list[tuple[int, int]] | None = None) -> Score:
    return Score(quad=quad_score(text), words=word_score(text, bounds) if bounds else 0.0)

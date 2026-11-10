"""Liber Primus pages: loading, and splitting runes from layout.

A :class:`Page` keeps the raw transcription so that a decryption (which only touches runes)
can be rendered back with the original word breaks, punctuation and line layout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Literal, get_args

import numpy as np

from .gematria import RUNE_TO_INDEX, IndexArray, indices_to_latin, indices_to_runes

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "pages"

WORD_SEPARATORS = frozenset("•⁘⁚⁖⁜ \t\n'\"")

# Section names in reading order; "unsolved" are the 0-57 page blocks not yet decrypted.
SolvedName = Literal[
    "0_warning",
    "0_welcome",
    "0_wisdom",
    "0_koan_1",
    "0_loss_of_divinity",
    "jpg107-167",
    "jpg229",
    "p56_an_end",
    "p57_parable",
]
UnsolvedName = Literal[
    "p0-2",
    "p3-7",
    "p8-14",
    "p15-22",
    "p23-26",
    "p27-32",
    "p33-39",
    "p40-53",
    "p54-55",
]
PageName = Literal[UnsolvedName, SolvedName]
SOLVED: tuple[str, ...] = get_args(SolvedName)
UNSOLVED: tuple[str, ...] = get_args(UnsolvedName)


@dataclass(frozen=True)
class Page:
    name: str
    raw: str
    runes: IndexArray = field(repr=False)
    rune_positions: tuple[int, ...] = field(repr=False)

    @classmethod
    def from_text(cls, name: str, raw: str) -> Page:
        positions = tuple(i for i, ch in enumerate(raw) if ch in RUNE_TO_INDEX)
        idx = np.fromiter((RUNE_TO_INDEX[raw[i]] for i in positions), dtype=np.uint8)
        return cls(name=name, raw=raw, runes=idx, rune_positions=positions)

    def __len__(self) -> int:
        return int(self.runes.size)

    def render(self, plain: IndexArray, latin: bool = True) -> str:
        """Re-insert ``plain`` (same length as ``runes``) into the original layout."""
        if plain.size != self.runes.size:
            raise ValueError(f"expected {self.runes.size} runes, got {plain.size}")
        chars = list(self.raw)
        for pos, value in zip(self.rune_positions, plain.tolist(), strict=True):
            chars[pos] = indices_to_latin([value]) if latin else indices_to_runes([value])
        return "".join(chars).replace("•", " ")

    def word_lengths(self) -> list[int]:
        """Rune count of each word, words being split by any separator."""
        lengths: list[int] = []
        run = 0
        for ch in self.raw:
            if ch in RUNE_TO_INDEX:
                run += 1
            elif ch in WORD_SEPARATORS and run:
                lengths.append(run)
                run = 0
        if run:
            lengths.append(run)
        return lengths

    def word_bounds(self) -> list[tuple[int, int]]:
        """(start, end) rune offsets of each word, in rune-index space."""
        bounds: list[tuple[int, int]] = []
        start = 0
        for n in self.word_lengths():
            bounds.append((start, start + n))
            start += n
        return bounds


def _path(name: str, data_dir: Path) -> Path:
    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"invalid page name {name!r}")
    path = (data_dir / f"{name}.txt").resolve()
    if path.parent != data_dir.resolve():
        raise ValueError(f"invalid page name {name!r}")
    return path


@cache
def load(name: str, data_dir: Path = DATA_DIR) -> Page:
    path = _path(name, data_dir)
    return Page.from_text(name, path.read_text(encoding="utf-8"))


def load_solution(name: str, data_dir: Path = DATA_DIR) -> Page:
    """Known plaintext (in runes) for a solved section."""
    if name not in SOLVED:
        raise KeyError(f"{name!r} has no published solution")
    return load(f"solved_{name}", data_dir)


def unsolved_pages(data_dir: Path = DATA_DIR) -> list[Page]:
    return [load(n, data_dir) for n in UNSOLVED]


def all_unsolved_runes(data_dir: Path = DATA_DIR) -> IndexArray:
    return np.concatenate([p.runes for p in unsolved_pages(data_dir)])

"""Regression: every solved LP section is reproduced rune for rune by its recipe."""

from __future__ import annotations

import numpy as np
import pytest

from lplab import corpus
from lplab import hypotheses as H
from lplab import known_plaintext as kp
from lplab.gematria import latin_to_indices
from lplab.solutions import RECIPES


@pytest.mark.parametrize("name", list(RECIPES))
def test_recipe_reproduces_solved_section_rune_for_rune(name: str) -> None:
    best = H.execute(RECIPES[name], top_k=1)[0]
    truth = corpus.load_solution(name).runes
    assert np.array_equal(best.plaintext, truth), best.detail


def test_welcome_interrupters_fit_divinity_with_zero_mismatches() -> None:
    ct = corpus.load("0_welcome").runes
    pt = corpus.load_solution("0_welcome").runes
    key = latin_to_indices("DIVINITY")

    skip, mismatches = kp.fit_interrupters(ct, pt, lambda j: int(key[j % key.size]))

    assert mismatches == 0
    rune_zero_hits = np.flatnonzero(ct == 0)
    skipped_occurrences = [i for i, pos in enumerate(rune_zero_hits) if skip[pos]]
    assert skipped_occurrences == [3, 4, 5, 6, 9, 10, 13, 17, 19, 20, 24]
    assert int(skip.sum()) == 11

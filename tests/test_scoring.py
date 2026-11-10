"""Candidate scoring: quadgram fitness, dictionary word hits and the promising gate."""

from __future__ import annotations

import numpy as np
import pytest

from lplab import corpus, scoring
from lplab.corpus import SOLVED


@pytest.mark.parametrize("name", SOLVED)
def test_every_solved_plaintext_is_promising(name: str) -> None:
    page = corpus.load_solution(name)
    s = scoring.score(page.runes, page.word_bounds())
    assert s.promising


@pytest.mark.parametrize("name", SOLVED)
def test_every_solved_plaintext_has_quad_above_minus_five(name: str) -> None:
    page = corpus.load_solution(name)
    assert scoring.quad_score(page.runes) > -5


def test_uniform_random_text_is_not_promising() -> None:
    rng = np.random.default_rng(3)
    text = rng.integers(0, 29, 300).astype(np.uint8)
    s = scoring.score(text)
    assert s.quad < scoring.QUAD_PROMISING
    assert not s.promising


def test_word_score_of_a_solved_page_exceeds_point_seven() -> None:
    page = corpus.load_solution("0_wisdom")
    assert scoring.word_score(page.runes, page.word_bounds()) > 0.7


def test_word_score_is_zero_without_word_bounds() -> None:
    page = corpus.load_solution("0_wisdom")
    assert scoring.score(page.runes).words == 0.0


def test_combined_score_is_the_average_of_normalised_quad_and_words() -> None:
    s = scoring.Score(quad=-8.5, words=1.0)
    assert s.combined == pytest.approx(0.5)
    assert scoring.Score(quad=-4.0, words=1.0).combined == pytest.approx(0.5 * 1.0 + 0.5)

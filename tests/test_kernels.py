"""Hot-loop kernels: quadgram scoring and periodic-key hill climbing, C and numba."""

from __future__ import annotations

import ctypes

import numpy as np
import pytest

from lplab import corpus, ngram
from lplab import kernels as K
from lplab.ciphers import encrypt_stream
from lplab.kernels import _nb_climb, _nb_quad_score


@pytest.fixture(scope="module")
def quad() -> np.ndarray:
    return ngram.load().quad


@pytest.fixture(scope="module")
def koan() -> np.ndarray:
    return corpus.load_solution("0_koan_1").runes


def test_quad_score_matches_ngram_model_on_a_page(quad: np.ndarray, koan: np.ndarray) -> None:
    model = ngram.load()
    assert K.quad_score(koan, quad) == pytest.approx(model.quad_score(koan), abs=1e-5)


def test_numba_quad_score_matches_c_kernel(quad: np.ndarray, koan: np.ndarray) -> None:
    lib = K._clib()
    c_value = lib.lp_quad_score(K._u8(koan), koan.size, K._f32(quad))
    nb_value = float(_nb_quad_score(koan, quad))
    assert nb_value == pytest.approx(c_value, abs=1e-5)


def test_quad_score_of_text_shorter_than_four_runes_is_floor(quad: np.ndarray) -> None:
    assert K.quad_score(np.array([1, 2, 3], dtype=np.uint8), quad) <= -1e29


def test_climb_periodic_recovers_period_seven_key(quad: np.ndarray, koan: np.ndarray) -> None:
    rng = np.random.default_rng(2024)
    key = rng.integers(0, 29, 7).astype(np.uint8)
    stream = np.resize(key, koan.size)
    ct = encrypt_stream(koan, stream)

    _score, recovered = K.climb_periodic(ct, 7, quad)

    assert np.array_equal(recovered, key)


def test_nb_climb_recovers_period_seven_key(quad: np.ndarray, koan: np.ndarray) -> None:
    rng = np.random.default_rng(2024)
    key = rng.integers(0, 29, 7).astype(np.uint8)
    ct = encrypt_stream(koan, np.resize(key, koan.size))

    _score, recovered = _nb_climb(
        ct, np.zeros(ct.size, dtype=np.bool_), 7, 1, 1, 0, quad, 8, 12, 1
    )

    assert np.array_equal(recovered, key)


def test_climb_periodic_rejects_period_zero(quad: np.ndarray, koan: np.ndarray) -> None:
    with pytest.raises(ValueError, match="period"):
        K.climb_periodic(koan, 0, quad)


def test_c_library_is_loadable_as_ctypes_cdll() -> None:
    assert isinstance(K._clib(), ctypes.CDLL)

"""Statistical fingerprints: IoC, doublets, periodic IoC and the unsolved-page anomaly."""

from __future__ import annotations

import numpy as np

from lplab import corpus, stats
from lplab.ciphers import encrypt_stream


def test_ioc_of_large_uniform_random_text_is_about_one() -> None:
    rng = np.random.default_rng(0)
    text = rng.integers(0, 29, 200_000).astype(np.uint8)
    assert abs(stats.ioc(text) - 1.0) < 0.1


def test_doublet_rate_of_constant_text_is_one() -> None:
    assert stats.doublet_rate(np.full(100, 3, dtype=np.uint8)) == 1.0


def test_doublet_rate_of_uniform_random_text_is_near_one_in_29() -> None:
    rng = np.random.default_rng(1)
    text = rng.integers(0, 29, 100_000).astype(np.uint8)
    assert abs(stats.doublet_rate(text) - 1 / 29) < 0.005


def test_periodic_ioc_peaks_at_multiple_of_the_vigenere_period() -> None:
    plain = corpus.load_solution("0_koan_1").runes
    key = np.random.default_rng(5).integers(0, 29, 5).astype(np.uint8)
    ct = encrypt_stream(plain, np.resize(key, plain.size))

    per = stats.periodic_ioc(ct, 40)
    best = int(np.argmax(per[1:]) + 1)

    assert best % 5 == 0


def test_unsolved_pages_have_a_doublet_deficit_below_1e_minus_50() -> None:
    p_value = stats.doublet_pvalue(corpus.all_unsolved_runes())
    assert p_value < 1e-50


def test_fingerprint_reports_length_and_consistent_statistics() -> None:
    text = corpus.load_solution("0_koan_1").runes
    fp = stats.fingerprint(text)

    assert fp.length == text.size
    assert fp.ioc == stats.ioc(text)
    assert fp.entropy == stats.entropy(text)
    assert fp.doublet_rate == stats.doublet_rate(text)
    per = stats.periodic_ioc(text, min(40, max(1, text.size // 8)))
    assert 1 <= fp.best_period < per.size
    assert fp.best_period == int(np.argmax(per[1:]) + 1)
    assert fp.best_period_ioc == per[fp.best_period]


def test_fingerprint_as_dict_has_exactly_the_documented_fields() -> None:
    fp = stats.fingerprint(corpus.load_solution("0_koan_1").runes)
    assert set(fp.as_dict()) == {
        "length",
        "ioc",
        "entropy",
        "doublet_rate",
        "doublet_pvalue",
        "best_period",
        "best_period_ioc",
    }

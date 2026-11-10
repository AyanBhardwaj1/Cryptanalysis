"""Tests for the research-driven additions: transform views, skip penalty, mechanism screen."""

from __future__ import annotations

import numpy as np

from lplab import ciphers as C
from lplab import corpus, simulate
from lplab import hypotheses as H
from lplab.gematria import N


def test_delta_view_undoes_ciphertext_feedback_autokey() -> None:
    page = corpus.load("p54-55")
    view = H.page_view("p54-55", "delta")
    prev = np.concatenate([[0], page.runes[:-1].astype(np.int64)])
    assert np.array_equal(view.runes, (page.runes.astype(np.int64) - prev) % N)
    assert view.raw == page.raw  # layout untouched


def test_delta_sum_view_adds_previous_rune() -> None:
    page = corpus.load("p54-55")
    view = H.page_view("p54-55", "delta_sum")
    assert int(view.runes[1]) == (int(page.runes[1]) + int(page.runes[0])) % N


def test_reverse_view_reads_back_to_front_and_keeps_word_lengths() -> None:
    page = corpus.load("0_warning")
    view = H.page_view("0_warning", "reverse")
    assert np.array_equal(view.runes, page.runes[::-1])
    assert view.word_lengths() == page.word_lengths()[::-1]


def test_reverse_transform_solves_a_reversed_atbash_page_view() -> None:
    # atbash is position-independent, so reading backwards must still decrypt every rune
    best = H.execute(H.AffineH(page="0_warning", affine_mode="atbash", transform="reverse"), 1)[0]
    truth = corpus.load_solution("0_warning").runes[::-1]
    assert np.array_equal(best.plaintext, truth)
    assert best.preview().startswith(H.page_view("0_warning", "reverse").render(truth)[:20])


def test_transform_changes_fingerprint() -> None:
    a = H.AffineH(page="p54-55")
    b = H.AffineH(page="p54-55", transform="delta")
    assert a.fingerprint() != b.fingerprint()


def test_skip_penalty_limits_spurious_interrupters_on_wrong_key() -> None:
    ct = corpus.load("p0-2").runes

    def wrong(sk: C.BoolArray) -> np.ndarray:
        return C.vigenere(ct, "CICADA", skip=sk)

    penalised, _ = H.refine_interrupters(ct, 0, wrong)
    free, _ = H.refine_interrupters(ct, 0, wrong, skip_penalty=0.0)
    assert penalised.sum() * 2 <= free.sum()


def test_skip_penalty_keeps_real_interrupters() -> None:
    best = H.execute(H.VigenereKeyH(page="0_welcome", keys=["DIVINITY"]), 1)[0]
    assert np.array_equal(best.plaintext, corpus.load_solution("0_welcome").runes)


def test_screen_reports_every_mechanism_and_random_text_doublet_rate() -> None:
    rows = {r.mechanism: r for r in simulate.screen(trials=4, length=800, seed=1)}
    assert set(rows) == set(simulate.MECHANISMS)
    assert abs(rows["one_time_pad"].doublet_rate - 1 / N) < 0.015
    assert rows["otp_no_doublets"].doublet_rate == 0.0


def test_screen_finds_no_standard_mechanism_matching_observed_doublets() -> None:
    rows = simulate.screen(trials=6, length=1200, seed=2)
    standard = [r for r in rows if r.mechanism != "otp_no_doublets"]
    assert not any(r.matches_observed for r in standard)


def test_doublet_fit_accepts_matching_rate_and_rejects_random_rate() -> None:
    obs = simulate.observed()
    assert simulate.doublet_fit_pvalue(obs.doublet_rate, obs) > 0.5
    assert simulate.doublet_fit_pvalue(1 / N, obs) < 1e-50


def test_observed_doublet_rate_is_far_below_random() -> None:
    assert simulate.observed().doublet_rate < 0.01

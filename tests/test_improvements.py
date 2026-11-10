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
    standard = [
        r for r in rows if r.mechanism != "otp_no_doublets" and "skip_if_same" not in r.mechanism
    ]
    assert not any(r.matches_observed for r in standard)


def test_doublet_fit_accepts_matching_rate_and_rejects_random_rate() -> None:
    obs = simulate.observed()
    assert simulate.doublet_fit_pvalue(obs.doublet_rate, obs) > 0.5
    assert simulate.doublet_fit_pvalue(1 / N, obs) < 1e-50


def test_observed_doublet_rate_is_far_below_random() -> None:
    assert simulate.observed().doublet_rate < 0.01


# --- skip-if-same rule ---------------------------------------------------------------------

from lplab import skiprule  # noqa: E402
from lplab.gematria import latin_to_indices  # noqa: E402


def _divinity_key(n: int) -> np.ndarray:
    return np.resize(latin_to_indices("DIVINITY"), 2 * n + 2)


def test_skip_rule_encrypt_with_q1_never_emits_doublets() -> None:
    pt = corpus.load_solution("0_koan_1").runes
    ct = skiprule.encrypt(pt, _divinity_key(pt.size), q=1.0)
    assert not np.any(ct[1:] == ct[:-1])


def test_skip_rule_q081_reproduces_observed_doublet_rate() -> None:
    pt = np.concatenate([corpus.load_solution(n).runes for n in corpus.SOLVED])
    rng = np.random.default_rng(7)
    key = rng.integers(0, N, 2 * pt.size + 2).astype(np.uint8)
    ct = skiprule.encrypt(pt, key, q=0.81, rng=rng)
    rate = float(np.mean(ct[1:] == ct[:-1]))
    assert 0.003 < rate < 0.012


def test_skip_rule_decode_recovers_plaintext_exactly() -> None:
    pt = corpus.load_solution("0_koan_1").runes
    key = _divinity_key(pt.size)
    for q in (1.0, 0.81):
        ct = skiprule.encrypt(pt, key, q=q, rng=np.random.default_rng(1))
        dec, n_skips = skiprule.decode(ct, key)
        assert np.array_equal(dec, pt)
        assert n_skips > 0


def test_skip_rule_decoder_leaves_ordinary_vigenere_alone() -> None:
    ct = corpus.load("0_welcome").runes
    skip = C.interrupter_mask(ct, 0, [3, 4, 5, 6, 9, 10, 13, 17, 19, 20, 24])
    dec, _ = skiprule.decode(ct, _divinity_key(ct.size), skip=skip)
    assert np.array_equal(dec, corpus.load_solution("0_welcome").runes)


def test_skip_rule_hypothesis_requires_matching_key_material() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        H.parse({"family": "skip_rule", "page": "p0-2", "key_source": "keyword"})
    with pytest.raises(ValidationError):
        H.parse({"family": "skip_rule", "page": "p0-2", "key_source": "sequence"})
    ok = H.parse({"family": "skip_rule", "page": "p0-2", "key_source": "sequence",
                  "sequence": "primes"})  # fmt: skip
    assert ok.family == "skip_rule"


def test_skip_rule_family_runs_on_a_page() -> None:
    h = H.SkipRuleH(page="p54-55", key_source="keyword", keys=["DIVINITY", "PRIMES"])
    cands = H.execute(h, top_k=2)
    assert len(cands) == 2
    assert all("key-skips=" in c.detail for c in cands)


def test_screen_skip_rule_q081_fits_and_plain_families_do_not() -> None:
    rows = {r.mechanism: r for r in simulate.screen(trials=6, length=1500, seed=5)}
    assert rows["vigenere_p8_skip_if_same_q081"].matches_observed
    assert not rows["one_time_pad"].matches_observed


# --- word boundaries and one-rune words --------------------------------------------------


def test_line_breaks_do_not_split_words() -> None:
    # "KNOWLEDGE" wraps across a line in A Warning's ciphertext; it must be one 9-rune word
    page = corpus.load("0_warning")
    sol = corpus.load_solution("0_warning")
    words = [sol.runes[s:e] for s, e in page.word_bounds()]
    target = latin_to_indices("KNOWLEDGE").tolist()  # C N O W L E D G E: 9 runes
    assert any(w.tolist() == target for w in words)


def test_one_rune_words_in_solved_text_are_a_or_i() -> None:
    from lplab.scoring import ONE_RUNE_WORDS

    singles = [
        int(corpus.load_solution(n).runes[s])
        for n in corpus.SOLVED
        for s, e in corpus.load(n).word_bounds()
        if e - s == 1
    ]
    share = np.mean([x in ONE_RUNE_WORDS for x in singles])
    assert len(singles) >= 25 and share > 0.95


def test_word_score_is_perfect_on_solved_and_near_zero_on_random() -> None:
    from lplab import scoring

    page = corpus.load("0_koan_1")
    assert scoring.word_score(corpus.load_solution("0_koan_1").runes, page.word_bounds()) == 1.0
    rnd = np.random.default_rng(0).integers(0, N, page.runes.size).astype(np.uint8)
    assert scoring.word_score(rnd, page.word_bounds()) < 0.1

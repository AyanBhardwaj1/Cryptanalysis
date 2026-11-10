"""Decryptors and keystreams over Z/29: affine maps, streams, Vigenere, autokey, sequences."""

from __future__ import annotations

import numpy as np
import pytest

from lplab import ciphers as C
from lplab import corpus
from lplab.gematria import latin_to_indices


def _random_runes(seed: int, n: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, 29, n).astype(np.uint8)


@pytest.mark.parametrize("a,b", [(1, 0), (3, 7), (5, 0), (12, 20), (28, 28), (28, 2)])
def test_affine_inverse_composes_to_identity(a: int, b: int) -> None:
    f = C.Affine(a, b)
    inv = f.inverse()
    x = np.arange(29, dtype=np.uint8)
    assert np.array_equal(inv.apply(f.apply(x)), x)
    assert np.array_equal(f.apply(inv.apply(x)), x)


def test_affine_with_zero_multiplier_raises_value_error() -> None:
    with pytest.raises(ValueError, match="non-zero"):
        C.Affine(0, 5)


@pytest.mark.parametrize("sign", [1, -1])
def test_stream_round_trip_with_affine_and_skip_mask(sign: int) -> None:
    rng = np.random.default_rng(42)
    n = 300
    pt = _random_runes(1, n)
    stream = rng.integers(0, 29, n).astype(np.uint8)
    skip = rng.random(n) < 0.15
    affine = C.Affine(5, 11)

    ct = C.encrypt_stream(pt, stream, sign=sign, affine=affine, skip=skip)
    back = C.decrypt_stream(ct, stream, sign=sign, affine=affine, skip=skip)

    assert np.array_equal(back, pt)


def test_skipped_positions_pass_through_decryption_unchanged() -> None:
    n = 200
    ct = _random_runes(2, n)
    stream = _random_runes(3, n)
    skip = np.zeros(n, dtype=np.bool_)
    skip[::7] = True

    pt = C.decrypt_stream(ct, stream, affine=C.Affine(3, 4), skip=skip)

    assert np.array_equal(pt[skip], ct[skip])


def test_decrypt_stream_does_not_mutate_its_inputs() -> None:
    ct = _random_runes(4, 50)
    stream = _random_runes(5, 50)
    ct_before, stream_before = ct.copy(), stream.copy()
    C.decrypt_stream(ct, stream, skip=np.arange(50) % 3 == 0)
    assert np.array_equal(ct, ct_before)
    assert np.array_equal(stream, stream_before)


def test_vigenere_with_string_key_equals_vigenere_with_index_key() -> None:
    ct = _random_runes(6, 120)
    by_str = C.vigenere(ct, "DIVINITY")
    by_idx = C.vigenere(ct, latin_to_indices("DIVINITY"))
    assert np.array_equal(by_str, by_idx)


def test_interrupter_mask_selects_only_listed_occurrences() -> None:
    ct = np.array([0, 1, 0, 2, 0, 0], dtype=np.uint8)  # rune 0 at positions 0, 2, 4, 5
    mask = C.interrupter_mask(ct, 0, [1, 3])
    assert np.flatnonzero(mask).tolist() == [2, 5]


def test_interrupter_mask_without_occurrences_marks_every_hit() -> None:
    ct = np.array([0, 1, 0, 2, 0, 0], dtype=np.uint8)
    assert np.flatnonzero(C.interrupter_mask(ct, 0)).tolist() == [0, 2, 4, 5]


def test_interrupter_mask_with_no_rune_marks_nothing() -> None:
    ct = np.array([0, 1, 0], dtype=np.uint8)
    assert not C.interrupter_mask(ct, None).any()


def test_primes_sequence_starts_2_3_5_7_11() -> None:
    assert C.sequence("primes", 5).tolist() == [2, 3, 5, 7, 11]


def test_totient_primes_sequence_is_prime_minus_one() -> None:
    assert C.sequence("totient_primes", 3).tolist() == [1, 2, 4]


def test_unknown_sequence_name_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unknown sequence"):
        C.sequence("lucas", 5)


def test_autokey_with_plain_feedback_matches_vigenere_on_primer_plus_plaintext() -> None:
    primer = latin_to_indices("DIVINITY")
    pt = _random_runes(7, 60)
    full_key = np.concatenate([primer, pt])
    ct = C.encrypt_stream(pt, full_key[: pt.size])

    recovered = C.autokey(ct, primer, feedback="plain")

    assert np.array_equal(recovered, pt)
    assert np.array_equal(recovered, C.vigenere(ct, full_key))


def test_running_key_raises_when_source_is_too_short() -> None:
    ct = _random_runes(8, 10)
    source = _random_runes(9, 5)
    with pytest.raises(ValueError, match="too short"):
        C.running_key(ct, source)


def test_running_key_decrypts_against_source_slice() -> None:
    pt = _random_runes(10, 20)
    source = _random_runes(11, 40)
    ct = C.encrypt_stream(pt, source[5:25])
    assert np.array_equal(C.running_key(ct, source, offset=5), pt)


def test_vigenere_output_has_the_same_length_as_the_ciphertext() -> None:
    page = corpus.load("0_welcome")
    out = C.vigenere(page.runes, "DIVINITY")
    assert out.size == page.runes.size

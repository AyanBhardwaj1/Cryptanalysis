"""The 29-rune Gematria Primus: alphabet, primes, transliteration and sums."""

from __future__ import annotations

import numpy as np

from lplab import gematria as G


def test_alphabet_has_29_runes() -> None:
    assert len(G.RUNES) == G.N == 29
    assert len(set(G.RUNES)) == 29


def test_primes_are_the_first_29_primes_in_increasing_order() -> None:
    primes = G.PRIMES
    assert primes[0] == 2
    assert primes[-1] == 109
    assert all(p > 1 and all(p % d for d in range(2, int(p**0.5) + 1)) for p in primes)
    assert list(primes) == sorted(primes)
    assert len(primes) == 29


def test_thing_transliterates_to_th_and_ing() -> None:
    assert G.latin_to_indices("THING").tolist() == [2, 21]


def test_know_transliterates_to_c_n_o_w() -> None:
    assert G.latin_to_indices("KNOW").tolist() == [5, 9, 3, 7]


def test_queen_starts_with_c_and_w() -> None:
    # Q is written CW in the LP and the U after it is absorbed into the digraph
    assert G.latin_to_indices("QUEEN").tolist()[:2] == [5, 7]


def test_runes_round_trip_through_indices() -> None:
    text = "".join(G.RUNES)
    idx = G.runes_to_indices(text)
    assert idx.dtype == np.uint8
    assert idx.tolist() == list(range(29))
    assert G.indices_to_runes(idx) == text


def test_indices_render_to_canonical_latin_readings() -> None:
    idx = G.runes_to_indices("ᚠᚢᚦᛝᛠ")
    assert G.indices_to_latin(idx) == "FUTHNGEA"


def test_non_rune_characters_are_dropped_from_runes_to_indices() -> None:
    assert G.runes_to_indices("ᚠ x ᚢ!\n").tolist() == [0, 1]


def test_gematria_sum_of_f_and_u_is_five() -> None:
    assert G.gematria_sum(G.runes_to_indices("ᚠᚢ")) == 5


def test_primes_of_maps_indices_to_prime_values() -> None:
    assert G.primes_of(np.array([0, 1, 28], dtype=np.uint8)).tolist() == [2, 3, 109]


def test_latin_to_indices_ignores_digits_and_punctuation() -> None:
    assert G.latin_to_indices("k9n, o!").tolist() == G.latin_to_indices("KNO").tolist()

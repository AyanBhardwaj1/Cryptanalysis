"""Hypothesis registry: validation of untrusted JSON, fingerprints and candidate records."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from lplab import corpus, scoring
from lplab import hypotheses as H


def test_parse_rejects_unknown_family() -> None:
    with pytest.raises(ValidationError):
        H.parse({"family": "rot13", "page": "p54-55"})


def test_parse_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        H.parse({"family": "affine", "page": "p54-55", "shell_command": "rm -rf /"})


def test_parse_rejects_unknown_page() -> None:
    with pytest.raises(ValidationError):
        H.parse({"family": "affine", "page": "0_nonexistent"})


def test_parse_rejects_period_max_below_period_min() -> None:
    with pytest.raises(ValidationError):
        H.parse({"family": "vigenere_climb", "page": "p54-55", "period_min": 10, "period_max": 5})


def test_parse_rejects_keywords_containing_digits() -> None:
    with pytest.raises(ValidationError):
        H.parse({"family": "vigenere_key", "page": "p54-55", "keys": ["ABC1"]})


def test_parse_rejects_interrupter_outside_rune_range() -> None:
    with pytest.raises(ValidationError):
        H.parse({"family": "affine", "page": "p54-55", "interrupter": 29})


def test_parse_accepts_a_json_string() -> None:
    raw = json.dumps({"family": "affine", "page": "p54-55", "affine_mode": "atbash"})
    h = H.parse(raw)
    assert isinstance(h, H.AffineH)
    assert h.affine_mode == "atbash"


def test_fingerprint_ignores_rationale() -> None:
    a = H.AffineH(page="p54-55", rationale="first reason")
    b = H.AffineH(page="p54-55", rationale="a completely different reason")
    assert a.fingerprint() == b.fingerprint()


def test_fingerprint_changes_when_a_parameter_changes() -> None:
    a = H.AffineH(page="p54-55", affine_mode="atbash")
    b = H.AffineH(page="p54-55", affine_mode="identity")
    assert a.fingerprint() != b.fingerprint()


def test_json_schema_has_a_discriminator_for_every_family() -> None:
    schema = H.json_schema()
    mapping = schema["discriminator"]["mapping"]
    assert set(mapping) == set(H.FAMILIES)


def test_candidate_as_dict_has_the_documented_keys() -> None:
    plaintext = corpus.load("p54-55").runes.copy()
    cand = H.Candidate(
        page="p54-55",
        family="affine",
        detail="a=1,b=0",
        plaintext=plaintext,
        score=scoring.Score(quad=-7.0, words=0.2),
    )
    assert set(cand.as_dict()) == {
        "page",
        "family",
        "detail",
        "quad",
        "words",
        "combined",
        "preview",
    }
    assert cand.as_dict()["quad"] == -7.0


def test_candidate_preview_is_the_rendered_page_layout() -> None:
    page = corpus.load("p54-55")
    cand = H.Candidate(
        page="p54-55",
        family="affine",
        detail="identity",
        plaintext=page.runes.copy(),
        score=scoring.Score(quad=-7.0, words=0.2),
    )
    assert cand.preview(20) == page.render(page.runes)[:20]

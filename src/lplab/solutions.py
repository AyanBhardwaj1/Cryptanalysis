"""Exact recipes for every solved LP section, as lab hypotheses.

These double as the lab's ground truth: ``lplab verify`` and the regression tests check that
each recipe, run blind through the normal search path (interrupters found automatically),
reproduces the published plaintext rune for rune.
"""

from __future__ import annotations

from . import hypotheses as H

RECIPES: dict[str, H.Hypothesis] = {
    "0_warning": H.AffineH(page="0_warning", affine_mode="atbash"),
    "0_welcome": H.VigenereKeyH(page="0_welcome", keys=["DIVINITY"]),
    "0_wisdom": H.AffineH(page="0_wisdom", affine_mode="identity"),
    "0_koan_1": H.AffineH(page="0_koan_1", affine_mode="shifts"),
    "0_loss_of_divinity": H.AffineH(page="0_loss_of_divinity", affine_mode="identity"),
    "jpg107-167": H.VigenereKeyH(page="jpg107-167", keys=["FIRFUMFERENFE"]),
    "jpg229": H.AffineH(page="jpg229", affine_mode="identity"),
    "p56_an_end": H.SequenceH(page="p56_an_end", name="totient_primes"),
    "p57_parable": H.AffineH(page="p57_parable", affine_mode="identity"),
}

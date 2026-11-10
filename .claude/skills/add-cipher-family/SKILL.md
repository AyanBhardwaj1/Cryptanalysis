---
name: add-cipher-family
description: Checklist and steps for adding a new attack family (cipher mechanism) to lplab - schema, decryptor, positive control, mechanism-screen entry, curriculum, planner prompt and tests. Use whenever a new cipher idea for the Liber Primus doesn't fit the existing families (affine, vigenere_key, vigenere_climb, sequence, autokey, running_key, skip_rule), or the user asks to support a new cipher, keystream rule, transposition, null/filler model or decoder.
---

# Add a cipher family to lplab

A family is only useful if the orchestrator can propose it safely, the runner can execute it
fast, and the lab can prove it would have found a planted key. Each step below protects one
of those. Work test-first: the positive-control test is written before the decoder.

## Steps

1. **Model it on paper.** Write encryption as a formula in the lab's terms
   (`x = (c - sign*k) mod 29; p = (a*x + b) mod 29`, interrupters, transforms) and say what
   it predicts for the doublet rate. If it can't get near 0.66%, it needs a rule that reacts
   to the ciphertext (see `src/lplab/skiprule.py` for the pattern).
2. **Reference encryptor + positive-control test (RED).** Put `encrypt(...)` next to the
   decoder (`ciphers.encrypt_stream` / `skiprule.encrypt` are the models). In
   `tests/test_<family>.py`, encrypt a solved plaintext (`corpus.load_solution(...)`) with a
   known key and assert the decoder returns it exactly. Run it and see it fail for the right
   reason.
3. **Decoder (GREEN).** Pure function over `uint8` index arrays, returning new arrays. Hot
   loops go in numba (`@njit(cache=True)`) or `kernels/lpkernel.c`; keep a numpy reference
   if you add C, and test that the two agree.
4. **Schema.** Add a pydantic class in `hypotheses.py` (`extra="forbid"`, `Literal` family,
   every numeric field bounded with `Field(ge=, le=)` so one hypothesis can't monopolise the
   machine; a `model_validator` for cross-field rules). Add it to the `Hypothesis` union and
   `FAMILIES`, and an `_execute_<family>` branch in `execute`. LLM output reaches this code,
   so it must reject anything it can't run.
5. **Screen entry.** Add a forward model to `simulate.MECHANISMS` so `lplab screen` reports
   whether the family can reproduce the page statistics.
6. **Wire it in.** A curriculum entry in `planner.curriculum` (cheap settings first), a line
   in the planner `SYSTEM_PROMPT` describing when it is worth proposing, and a solved-page
   recipe in `solutions.py` if a solved page uses it.
7. **Verify.** `.venv/bin/pytest -q`, `.venv/bin/ruff check src tests`, `.venv/bin/mypy src`,
   `.venv/bin/lplab verify` (still 9/9). Send the diff to the `reviewer` agent.
8. **Record** the decision in `docs/decisions.md` (what the family models and why it exists).

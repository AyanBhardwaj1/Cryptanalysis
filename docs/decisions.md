# Decisions

Settled choices, so they aren't argued again. Newest first.
Format: `- [YYYY-MM-DD] Decision. Why: reasoning. (Revisit if: condition)`

- [2026-11-10] Use an Opus orchestrator with Haiku workers. Why: Haiku costs a fraction of Opus per token, and the orchestrator checks every result. (Revisit if: workers keep failing checks on a kind of task, in which case give that agent a stronger model.)
- [2026-11-10] Model every cipher as affine-over-keystream with interrupters. Why: all 9 solved sections fit it exactly, so one engine + regression tests covers them. (Revisit if: a family needs non-additive structure, e.g. transposition.)
- [2026-11-10] LLM output is validated into bounded pydantic hypotheses and never executed. Why: model output is untrusted; bounds stop one proposal from monopolising compute. (Revisit if: never for the "no code execution" part.)
- [2026-11-10] Prioritise mechanisms that reproduce the 0.66% doublet rate (skip_rule, transforms). Why: plaintext-independent additive keys can't go below ~1.3% doublets, and community ledgers already swept them. (Revisit if: the transcription's doublet count is shown to be wrong.)
- [2026-11-10] Line breaks are layout, not word breaks. Why: the LP wraps words across lines; treating them as breaks broke the word score and one-rune-word stats. 
- [2026-11-10] Skip-rule decoder has no skip penalty by default. Why: measured, the penalty barely cut spurious skips (9 -> 8) and broke exact recovery on short periodic keys. (Revisit if: wrong-key candidates crowd out the top of the table.)

# Progress

## Done
- Core lab: gematria, corpus, unified cipher engine, interrupter detection, rune-space
  quadgrams + vocabulary, C kernel with numba fallback, stats, hypothesis registry, SQLite
  store, parallel runner, CLI. `lplab verify` reproduces 9/9 solved sections blind.
- Claude orchestration: Opus planner with schema-validated JSON plans, Haiku keyword and judge
  workers, cost ledger + budget cap, heuristic planner for offline runs, breakthrough file.
- Deep research (reports/, research_notes/): doublet deficit is the key constraint; community
  ledgers have exhausted plain additive families.
- Research-driven additions: mechanism screen (`lplab screen`), `skip_rule` family with an
  LM-guided decoder (exact recovery on planted keys at q=1.0 and 0.81), ciphertext transforms,
  interrupter skip penalty, line-wrap-aware word bounds, one-rune A/I rule, HTML report.
- Project skills: `run-experiment`, `add-cipher-family` (each with an eval case).

## Next
- Run `lplab orchestrate --planner claude` with an API key and a budget; nothing has been run
  against the live API yet (no key in the build session).
- Run the skill eval cases (`claude plugin eval .` from each skill dir) and review.
- Filler/null-rune decoder (word-length anomaly: 15.5% two-rune words vs ~23% English).
- Why ~19% of doublets survive: test triggers for the skip rule (Latin-letter comparison,
  lag-2 comparison, gated by interrupters).
- Key-reuse test at the repeated 6-gram D-J-U-B-E-I.
- Word-separator-aware (30-symbol) n-gram model; simulated annealing for running keys.
- Diff `data/pages` against rtkd/iddqd master transcription (erratum BELEIUE -> BELIEUE).

## Log
- [2026-11-10] Omega setup added (CLAUDE.md, docs, builder/reviewer agents, reflect skill).
- [2026-11-10] Built lplab core + Claude orchestrator; deep research; skip-rule family,
  mechanism screen, scoring fixes, report, project skills. Heuristic smoke runs only: best
  combined ~0.07 (noise level, as expected).

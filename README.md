# Cryptanalysis: a Liber Primus lab

A Python lab for attacking the unsolved pages of Cicada 3301's *Liber Primus* (LP). Fast,
deterministic search code (numpy, scipy, numba, plus a C kernel for the hot loops) does the
arithmetic. A Claude orchestrator (Opus) plans what to try, and Haiku workers brainstorm key
material and judge candidate plaintexts. The planner's output is data, not code: every
proposal is validated against a registry of bounded attack families before anything runs.

**Where it stands:**
- `lplab verify` reproduces all 9 solved LP sections blind, finding the interrupter positions
  automatically.
- The unsolved pages are still unsolved. The lab's job is to search well and rule things out
  honestly.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/lplab verify          # 9/9 solved sections through the normal search path
.venv/bin/lplab stats           # IoC, entropy, doublet rate per unsolved section
.venv/bin/lplab screen          # which cipher mechanisms can reproduce the page statistics
.venv/bin/lplab orchestrate --planner heuristic --rounds 5        # offline, no API key
ANTHROPIC_API_KEY=... .venv/bin/lplab orchestrate --planner claude --rounds 20 --budget 5
.venv/bin/lplab top -n 10       # best candidates so far (runs/lab.sqlite)
.venv/bin/lplab report          # HTML report: anomaly charts, mechanism screen, candidates
.venv/bin/lplab attack '{"family":"skip_rule","page":"p54-55","key_source":"sequence","sequence":"totient_primes"}'
.venv/bin/lplab crib --page 0_welcome --text WELCOME   # keystream implied by a guess
```

Tests: `.venv/bin/pytest -q` (155 tests). Lint and types: `ruff check src tests && mypy src`
(strict).

## How it works

```
             ┌──────────── Opus planner (ClaudePlanner) ────────────┐
 lab notebook│ page fingerprints, what was tried, best candidates,  │ JSON plan
 (SQLite) ──►│ mechanism screen, last round's validation errors     ├──────────┐
             └──────────────────────────────────────────────────────┘          │
                                                                               ▼
   Haiku KeywordWorker ◄── keyword_tasks           hypotheses.parse(): strict pydantic
   (parallel) ── keys ──► more hypotheses ───────► schemas, bounded params, dedup by hash
                                                                               │
                         runner: process pool ◄────────────────────────────────┘
                         hypotheses.execute(): ciphers + C/numba kernels,
                         interrupter search, skip-rule decoder, scoring
                                     │
   Haiku JudgeWorker ◄── promising candidates ── store ──► BREAKTHROUGH.md if judged ≥ 0.8
```

- **One cipher engine.** Every solved LP cipher fits one formula: `x = (c − sign·k) mod 29`,
  then `p = (a·x + b) mod 29`, with some ᚠ "interrupter" runes passed through without
  advancing the key. Atbash, the koan shift, Vigenère DIVINITY / FIRFUMFERENFE and the
  φ(prime) stream are all special cases (`src/lplab/ciphers.py`).
- **Scoring.** Two signals are combined:
  - Rune-space quadgram fitness, trained on public-domain English plus the solved LP text.
    English scores about −4.2 and random text about −8.4.
  - A word score over the original word breaks: dictionary words, and one-rune words must
    be A or I. Solved pages score 1.0, random text about 0.02.
- **Families:**
  - `affine`, `vigenere_key`, `vigenere_climb` (C hill-climber), `sequence` (primes,
    totients, Fibonacci, ...), `autokey`, `running_key`.
  - `skip_rule`: a keystream that burns a key element whenever the output would repeat the
    previous rune, with a decoder guided by the language model.
  - Any family can be combined with a `transform`: `delta`, `delta_sum` or `reverse`.

## What the research changed

The deep-research report is in [`reports/`](reports/Liber%20Primus%20cryptanalysis%20frontier.md);
the notes behind it are in `research_notes/`.

**The constraint.** The unsolved pages have 86 doublets (the same rune twice in a row),
where about 446 are expected (0.66% against 3.45%). No additive key that is independent of
the plaintext can go below about 1.3% on English. `lplab screen` confirms this: of 12
mechanisms tested, only a keystream with a skip-if-same rule firing about 81% of the time
reproduces it. That is why the `skip_rule` family exists.

**Fixes from the research:**
- Line breaks no longer split words.
- One-rune words must decrypt to A or I.
- Each spurious interrupter is penalised.
- Corrected explanation of the doublet anomaly.

## Working with Claude Code (Omega setup)

The project follows an orchestrator/worker setup:
- `CLAUDE.md` holds the rules and commands.
- `docs/` holds the progress log, decisions and known issues.
- `.claude/agents/` holds the Haiku `builder` and `reviewer` agents.
- `.claude/skills/` holds `reflect`, `run-experiment` and `add-cipher-family`.

Start a session with "read the docs, then plan X and brief the builders", and end it with
`/reflect`.

## Data and credits

The rune transcription is relikd's [LiberPrayground](https://github.com/relikd/LiberPrayground).
The n-gram tables come from the public-domain NLTK Gutenberg sample. See `data/README.md`.

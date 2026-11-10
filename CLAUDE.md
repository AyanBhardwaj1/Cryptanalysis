# Cryptanalysis (Liber Primus lab)

A Python cryptanalysis lab aimed at the unsolved pages of Cicada 3301's Liber Primus (LP).
Deterministic attack code (numpy/scipy/numba, plus a C kernel for the hot loops) does the
search; a Claude orchestrator (Opus) plans hypotheses and Haiku workers expand and judge them.
Every cipher family is regression-tested against the LP pages that are already solved.

## Stack and commands
- Stack: Python 3.11+, numpy, scipy, numba, C (gcc, loaded via ctypes), anthropic SDK, sqlite3
- Install: `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'`
- Run: `.venv/bin/lplab --help` (e.g. `lplab stats`, `lplab verify`, `lplab attack`, `lplab orchestrate`)
- Test: `.venv/bin/pytest -q`
- Lint/typecheck: `.venv/bin/ruff check src tests && .venv/bin/mypy src`
- Rebuild C kernel: `.venv/bin/lplab build-kernel` (also built lazily on first use)

## Where things live
- `src/lplab/gematria.py`   Gematria Primus: 29 runes, Latin values, primes
- `src/lplab/corpus.py`     loads `data/pages/*.txt`, splits runes from separators
- `src/lplab/ciphers.py`    vectorised decryptors (shift, atbash, vigenere, autokey, totient, ...)
- `src/lplab/stats.py`      IoC, entropy, doublets, periodic IoC, chi-squared
- `src/lplab/ngram.py`      rune-space n-gram language model (`data/ngrams.npz`)
- `src/lplab/kernels/`      C kernel + numba fallback for scoring and hill-climbing
- `src/lplab/hypotheses.py` registry of attack families with validated parameter schemas
- `src/lplab/store.py`      sqlite results DB (`runs/lab.sqlite`), dedups hypotheses
- `src/lplab/orchestrator.py`, `workers.py`  Claude planner (Opus) + Haiku workers
- `data/pages/`             LP transcription (from relikd/LiberPrayground), `solved_*` = known plaintext
- `docs/progress.md`      what's done, what's next, one dated log line per session
- `docs/decisions.md`     settled decisions, with date and reasoning
- `docs/known-issues.md`  gotchas and their fixes
- `.claude/agents/`       worker agents (Haiku, one job each)
- `.claude/skills/`       one folder per repeatable task, each with a SKILL.md

## Project rules
- A new cipher family is not done until it reproduces at least one solved page, or has a
  round-trip test (encrypt -> decrypt) if no solved page uses it.
- LLM output never executes as code: it is parsed into a registered hypothesis schema and
  validated before any attack runs. Unknown families are rejected.
- Never commit API keys or `runs/` output. Keys come from the environment only.
- Rune indices are always 0..28 in Gematria order (F=0 ... EA=28); keep arrays `uint8`.

## Orchestration
The main session is the orchestrator. Its job is to plan, split work, write briefs, and verify. It hands bulk work (writing or editing many files, mechanical refactors, broad searches, long test runs) to a worker whenever a worker can do it, and does work itself only when it's small or needs judgment the brief can't carry.

Workers:
- `builder` writes code to a brief, runs the brief's check, and reports the exact command and output.
- `reviewer` compares a diff against a brief and reports what matches, what's missing and what's out of scope. It never edits.

Every brief has this shape:
    Goal: [one or two sentences]
    Read first: [specific files]
    Constraints: [what not to touch, conventions to follow]
    Done when: [a command whose output proves it, or something visible to check]

Before accepting a worker's output, rerun its `Done when:` check yourself. If it fails, send a corrected brief. Don't patch quietly around it.
Send any non-trivial diff to `reviewer` before calling the task done.
Independent briefs can run in parallel. Dependent ones run in order.

## Session routine
Start: read `docs/progress.md`, `docs/decisions.md` and `docs/known-issues.md` before planning.
End:
1. Add a dated line to the log in `docs/progress.md` and update Done/Next.
2. Record any settled decision in `docs/decisions.md` (date, decision, why).
3. Record any gotcha in `docs/known-issues.md` (symptom, cause, fix).
4. Run `/reflect` and apply its proposed edits only after the user says OK.

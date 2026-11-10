# Known issues

Gotchas and their fixes. Read at session start.
Format: `- **Symptom**: cause → fix (YYYY-MM-DD)`
- **Interrupter search finds 13-18 "interrupters" on wrong keys**: greedy search overfits by deleting key steps → per-skip penalty `SKIP_PENALTY=0.25` in `refine_interrupters` (2026-11-10)
- **Greedy interrupter/skip decisions misalign after clustered events**: undecided later branch points default to "no", corrupting the lookahead window → decide jointly over the next few branch points in the window (2026-11-10)
- **mypy rejects `Literal[tuple]` page names and lambdas in comprehensions**: → `Literal[...]` aliases in corpus/ciphers with `get_args`, closure factory functions in hypotheses.py (2026-11-10)
- **Ruff strips `# noqa: BLE001`** (rule not selected): keep the explanation as a normal comment instead (2026-11-10)
- **Research sites blocked from cloud sessions** (uncovering-cicada fandom, web.archive.org, arxiv, cryptool): research relied on GitHub repos; allow those hosts in the environment to go deeper (2026-11-10)
- **`sqlite3.ProgrammingError` from Haiku keyword threads**: store connection was thread-bound → `check_same_thread=False` + one RLock around every access (2026-11-10)
- **A skip-rule sweep over all sequences takes ~11 min on 4 cores**: LM-guided decode ~0.1 s per variant → keep `affine_mode` identity unless the planner has a reason (2026-11-10)

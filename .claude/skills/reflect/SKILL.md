---
name: reflect
description: End-of-session review. Lists what went wrong this session and proposes the smallest edit to CLAUDE.md, a skill, an agent, or docs/known-issues.md that would prevent it next time, then waits for approval. Use when the user types /reflect, at the end of a work session, or after a worker failed a check or the user corrected Claude.
---

# Reflect

1. Look back over this session. List what went wrong or was slow: failed checks, briefs that were misunderstood, user corrections, repeated work, gotchas you hit. Keep each item to one line and give its cause.
2. For each item that is likely to happen again, propose the **smallest** fix and where it goes:
   - a rule in `CLAUDE.md` (only if it applies to most sessions)
   - a line in `docs/known-issues.md` (project-specific gotchas)
   - an edit to `.claude/agents/<worker>.md` (if a worker keeps making the same mistake)
   - a new or edited `.claude/skills/<task>/SKILL.md` (if a multi-step task keeps recurring)
   Show each fix as an exact before → after edit.
3. Skip one-off accidents. Not every mistake needs a rule, and a bloated CLAUDE.md costs tokens on every turn.
4. **Stop and wait.** Apply only the fixes the user approves, exactly as approved.
5. Make sure today's line is in `docs/progress.md`.

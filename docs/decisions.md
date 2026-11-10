# Decisions

Settled choices, so they aren't argued again. Newest first.
Format: `- [YYYY-MM-DD] Decision. Why: reasoning. (Revisit if: condition)`

- [2026-11-10] Use an Opus orchestrator with Haiku workers. Why: Haiku costs a fraction of Opus per token, and the orchestrator checks every result. (Revisit if: workers keep failing checks on a kind of task, in which case give that agent a stronger model.)

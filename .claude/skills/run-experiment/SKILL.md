---
name: run-experiment
description: Design, brief, run and verify one cryptanalysis experiment against the unsolved Liber Primus pages with lplab, through the lab's gates (mechanism screen, positive control, duplicate check, judged results). Use whenever the user wants to try a cipher idea, key, crib, keystream or "what if they used X" on the LP, run the orchestrator, check whether an idea was already tried, or interpret lplab results, even if they never say "experiment".
---

# Run an LP experiment

Most LP ideas have been tried, and a statistic can look exciting on gibberish. An experiment
is only worth reporting if it has passed through the same gates every time, so results stay
comparable across sessions. Read `docs/progress.md` first: it holds what was tried last.

## 1. State the hypothesis as data

Write it as one JSON object that `lplab.hypotheses.parse` accepts (families: affine,
vigenere_key, vigenere_climb, sequence, autokey, running_key, skip_rule; options: sign,
affine_mode, interrupter / interrupt_mode, transform). If the idea doesn't fit any family, it
is a new family: use the `add-cipher-family` skill instead of bending an existing one.

## 2. Gate it before spending compute

- **Doublet screen.** The unsolved pages have 0.66% doublets; any plaintext-independent
  additive key gives >1.3%. If the idea is a plain additive keystream, say so and wrap it in
  `skip_rule` or a `transform` instead. `lplab screen` shows which mechanisms fit.
- **Already tried?** Check `lplab top --db runs/lab.sqlite` / the store's fingerprint (the
  runner dedups automatically) and `reports/Liber Primus cryptanalysis frontier.md` for
  community negative results (OEIS, PRNG seeds, ~200 books, autokey lag <= 8).
- **Positive control.** Encrypt a solved page under the same mechanism with a known key
  (`lplab.skiprule.encrypt`, `ciphers.encrypt_stream`) and confirm the decoder recovers it.
  A decoder that can't find a planted key can't find a real one; this is the step most often
  skipped and the one that matters most.

## 3. Run

- One hypothesis: `lplab attack '<json>' --top 5`
- A batch / all day: `lplab orchestrate --planner claude --rounds N --budget USD` (needs
  `ANTHROPIC_API_KEY`; Opus plans, Haiku brainstorms keys and judges) or `--planner heuristic`
  offline. Results land in `runs/lab.sqlite`.
- For bulk sweeps, brief the `builder` agent with a `Done when:` that is a command you rerun.

## 4. Read the result honestly

- English scores ~ -4.2 quad and ~1.0 words; random ~ -8.4 and ~0.02. Anything below
  combined 0.45 is noise, whatever the preview looks like.
- A candidate is only interesting if the word score is high **at the original word breaks**
  and the one-rune words are A or I. Check `runs/BREAKTHROUGH.md` only exists after the judge
  rated >= 0.8, and re-derive it by hand before telling anyone.
- `lplab report` renders the anomaly charts and the best candidates.

## 5. Record

Add a dated line to `docs/progress.md` (what was run, best combined score, verdict), and any
gotcha to `docs/known-issues.md`. Negative results are results: they stop the next session
repeating the work.

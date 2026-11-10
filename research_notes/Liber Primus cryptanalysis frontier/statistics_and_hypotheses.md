# Statistical properties of the unsolved Liber Primus pages and the cipher hypotheses they support or rule out

Compiled 2026-11-10. Two kinds of evidence appear below, and they are labelled:

- **[MEASURED-LOCAL]**: computed during this research on the lab's own transcription, `/home/user/Cryptanalysis/data/pages/*.txt`, which comes from [relikd/LiberPrayground](https://github.com/relikd/LiberPrayground). The unsolved set is the 9 sections p0-2 … p54-55: 12,956 runes, 3,320 separator-delimited tokens and 59 blank-line-delimited page chunks. The scripts are in the session scratchpad (`lpstats.py`, `lpstats2.py`, `sim.py`, `wl.py`, `per.py`) and can be re-run with `.venv/bin/python`.
- **[REPORTED]**: claims from external sources. Nearly all of these are hobbyist or "AI-lab" GitHub repositories from 2026. They are self-reported, not peer-reviewed, and should be treated as claims.

Access limits: the Uncovering Cicada fandom wiki, web.archive.org and boxentriq.com were not reachable from this session (DNS or proxy refusal). Wiki content therefore appears only through search-engine snippets. I found no Reddit thread, Crypto.SE post or peer-reviewed paper on the LP statistics.

---

## 1. The doublet deficit: what is measured, where it was reported, and which mechanisms produce it

### Takeaway
The unsolved pages contain 86 adjacent identical runes. About 446 would be expected if adjacent runes were independent: 0.66% vs 3.45%, z ≈ −17.4, binomial p ≈ 3e−99. This is the only strong non-random signal in the corpus. The suppression is uniform across pages, sections, word boundaries and line breaks, and the difference histogram over 1..28 is flat. Any additive or affine cipher whose key is statistically independent of the plaintext cannot drive the rate this low, since the floor is about 1.3–1.8% for English-like plaintext. The encryption must therefore use the ciphertext or the plaintext: a chain cipher, a re-draw/skip rule, or a post-hoc rewrite. A "key that never repeats the previous shift" does **not** produce the deficit.

### Cited Findings
**The measurement**
- [MEASURED-LOCAL] Unsolved total: 12,956 runes and 12,947 within-section adjacent pairs. 86 doublets, a rate of 0.664%. Expected at 1/29: 446.4. z = −17.36; binomial lower-tail p = 2.9e−99. — [relikd/LiberPrayground transcription](https://github.com/relikd/LiberPrayground), measured 2026-11-10
- [REPORTED] The same figures appear independently: "86 times where 447 are expected (0.66% vs. 3.45%, z = -17)" over 12,956 runes. The README says the work was done 6–7 Sept 2026. — [Leo-Y-Zhang/LiberPrimusAnalysis](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis)
- [REPORTED] "Doubled runes: 86 observed vs 445 expected (0.19 of uniform). Solved pages sit at 0.86. A soft re-draw model gives 0.81 and survives." Repository paused 2026-11-01. — [RiskAverseTech/cicada-ioc STATUS.md](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md)
- [REPORTED] "Adjacent-equal ('doublet') rate 0.66–0.68%" vs 3.45%, called "the only real structure in the entire corpus". IoC·N = 1.000, entropy 4.857 bits (max 4.858). Status as of 2026-11-05. — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)
- [REPORTED] A search snippet of the Uncovering Cicada wiki: "the bigram distribution of Liber Primus as a whole reveals a lower than expected number of doublets", and the doublet rate of random text is "1/29 = 3.45%". The page could not be fetched, so I could not confirm its date or author. — [Uncovering Cicada wiki: Frequency Analysis Unsolved Pages](https://uncovering-cicada.fandom.com/wiki/Frequency_Analysis_Unsolved_Pages)

**Per-section and per-page variation (the "some pages ~0.5%, others ~1%" question)**
- [MEASURED-LOCAL] Per-section doublet rates: p0-2 0.55%, p3-7 0.52%, p8-14 0.52%, p15-22 0.53%, p23-26 1.08%, p27-32 0.91%, p33-39 0.71%, p40-53 0.60%, p54-55 0.98%. Across sections the variation is consistent with one common rate (heterogeneity χ² = 6.19, df 8, p = 0.63). — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] Across 59 page chunks, the rates run from 0% (16 chunks) to 2.15%. The heterogeneity χ² is 62.7 on df 58, p = 0.31. A Poisson model at 0.667% with ~200–270 pairs per page predicts about 15 zero-doublet pages, and 16 are observed. The apparent split between 0.5% pages and 1% pages is sampling noise. — [relikd transcription](https://github.com/relikd/LiberPrayground)

**Where the surviving doublets sit**
- [MEASURED-LOCAL] Within-word pairs: 60/9,636 = 0.62%. Pairs across a word separator: 26/3,311 = 0.79%. Pairs across a line break: 4/585 = 0.68%. The suppression therefore runs continuously across word and line boundaries and does not reset per word or per line. No triple-rune run occurs. The 86 doublets are spread across 28 of the 29 runes (most common: AE 7, X 6, W 6, G 5), and F appears in 4 of them. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] Only lag 1 is suppressed. Coincidence rates at lags 2–7 are 3.40%, 3.39%, 3.54%, 3.70%, 3.51% and 3.48%, all at the 3.45% baseline. P(Δ[i] = Δ[i−1]) = 3.37%, also normal. — [relikd transcription](https://github.com/relikd/LiberPrayground)

**The difference (step) distribution**
- [MEASURED-LOCAL] Δ = c[i] − c[i−1] mod 29 has 86 at Δ=0 and between 404 and 510 in each of Δ=1..28. Against uniform on 1..28: χ² = 41.4, df 27, p = 0.038, which is mildly non-uniform and does not survive multiple-testing caution. The largest deviations are Δ=17 (z −2.6), Δ=9 (+2.35), Δ=2 and Δ=13 (+2.07). Δ is independent of the preceding rune (29×28 contingency χ² = 774.6, df 756, p = 0.31). — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [REPORTED] "The step between consecutive runes is uniform on 1..28 and independent of the preceding rune." — [Leo-Y-Zhang/LiberPrimusAnalysis](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis)

**Solved pages as controls**
- [MEASURED-LOCAL] Ciphertext doublet rates on the solved sections: 0_welcome (Vigenère, key DIVINITY) 3.11%; 0_warning 2.73%; 0_koan_1 1.80%; 0_loss_of_divinity 2.39%; jpg107-167 2.83%; p56_an_end (totient-prime stream) 2.38% (2/84); p57_parable (plaintext) 1.06% (1/94). The rune-encoded plaintext of all solved pages has a doublet rate of 2.59% over 2,979 runes. None of Cicada's known methods suppresses doublets. — [relikd transcription](https://github.com/relikd/LiberPrayground)

**Mechanism simulations** [MEASURED-LOCAL; plaintext is ~101k runes of English (vim user-manual prose) transliterated to Gematria Primus, plus the LP solved plaintext]

| Mechanism | Ciphertext doublet rate |
|---|---|
| Vigenère, uniform random key | 3.51% |
| Random key with k[i] ≠ k[i−1] ("never repeats the previous shift") | **3.44%**: no suppression |
| English running key, c = p + q | 3.95%: doublets *enhanced* |
| English running key, c = p − q or c = q − p (Beaufort) | 3.39% |
| Plaintext autokey c = p[i] + p[i−1] | 4.57% |
| Ciphertext autokey c = p[i] + c[i−1], no key | 2.56%. Doublet iff p = F. The Δ histogram equals the plaintext distribution (bins range from 3 to 12,009), which is grossly non-flat. |
| Ciphertext autokey plus random key, c = p + k + c[i−1] | 3.43% |
| Totient-prime stream (the p56 "An End" method) | 3.21% |
| Chain cipher c[i] = c[i−1] + ((p+k) mod 28) + 1 | 0.00% |
| Vigenère with "skip key if c[i] = c[i−1]" (re-draw) | 0.00% |

The simulations ran 2026-11-10 using this lab's `lplab.ciphers` and `lplab.gematria` with the [relikd transcription](https://github.com/relikd/LiberPrayground).

**A lower bound that holds for any plaintext-independent key** [MEASURED-LOCAL]
- For c = p + k, a doublet occurs iff Δk = −Δp. So P(doublet) = Σ_d P(Δp=d)·P(Δk=−d) ≥ min_d P(Δp=d), for **any** key-difference distribution independent of the plaintext. That includes non-uniform, non-stationary, PRNG and running-key sources. Beaufort (Δk = Δp) and fixed-multiplier affine ciphers obey the same bound.
- Measured floor: min_d P(Δp=d) = 1.80% for English prose (d = 18) and 1.31% for the LP solved plaintext (d = 7). The minimum over all affine multipliers is the same.
- Observed 0.66% is far below both floors. **Conclusion: if the plaintext is English-like rune text, the keystream, or a post-processing step, must depend on the plaintext or ciphertext.** — [relikd transcription](https://github.com/relikd/LiberPrayground)

**Mechanisms proposed by others**
- [REPORTED] Leo-Y-Zhang: "Any cipher adding a ciphertext-independent key gives about 3.4% doublets on English. Only a chain cipher, where each rune is the previous rune plus a non-zero step from a flat, aperiodic 28-symbol keystream, reproduces the observed fingerprint." Described as supported, not confirmed. — [Leo-Y-Zhang/LiberPrimusAnalysis](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis)
- [REPORTED] Dukotah proposes "a soft rejection-sampling or anti-repeat filter (about 83% suppression, p_keep ≈ 0.18) applied to a memoryless base". He calls it a "Smirnov word / Carlitz composition" and reports it as machine-applied (Round 17, power ≥ 0.99). He also cautions (Round 12) that "a soft anti-repeat rewrite of the output can set the doublet rate by itself", so "the deficit does not identify the key type". A "skip_by_two" doublet prior from Round 18 did not replicate (Round 33). — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)
- [REPORTED] RiskAverseTech: a "soft re-draw model gives 0.81 and survives". The fitted re-draw probability of 0.81 matches 1 − 0.66/3.45 = 0.807. — [RiskAverseTech STATUS.md](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md)

### Inferences
- **The required suppression is about 81%, not 100%.** A hard rule (chain cipher or deterministic skip) would give 0 doublets. The 86 survivors would then need a transcription error rate of roughly 0.66% × 29/2 ≈ 9.6%, which contradicts the reported "99.7% held-out glyph accuracy" ([RiskAverseTech](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md)). So either the rule is probabilistic, as in a soft re-draw with p_keep ≈ 0.19, or a deterministic rule fails at about 19% of positions for a reason we cannot see in the ciphertext. That reason is not word boundaries, line breaks, page or section, since suppression is uniform across all of them. It could be something such as "the rule is checked in a different representation" or "the rule only fires when a secondary condition holds, which happens about 81% of the time".
- **The common hypothesis "the key never repeats the previous shift" is wrong.** It changes nothing: 3.44% in simulation. This lab's `src/lplab/stats.py` module docstring repeats the error and should be corrected.
- Ciphertext autokey without a secondary key is ruled out by the flat Δ histogram. With an independent secondary key it no longer suppresses doublets (3.43%).
- Most mechanisms consistent with all the measurements share one shape: c[i] = c[i−1] + s[i], or a Vigenère with a rejection on c[i] = c[i−1]. In both, the encryptor *looked at* the previous ciphertext rune. This points to a computer-implemented cipher, consistent with Dukotah's "machine-applied" claim. A hand cipher using a 29×29 tableau could also include a "never write the same rune twice" convention, but a convention applied by hand would be expected to be hard (0%) rather than 81%.

### Gaps
- I could not establish who first reported the doublet deficit, or when. The Uncovering Cicada wiki page ("Frequency Analysis Unsolved Pages") is the earliest community source surfaced, but its history and date were unreachable (fandom and web.archive.org blocked). No Reddit thread surfaced. My belief that the observation dates to the 2014–2017 solving era is unverified.
- I found no published or academic analysis of ciphers that suppress doublets, and no Crypto.SE thread on the LP doublet constraint. George Lasry's published work in the search results concerns columnar transposition, not running key or autokey detection.
- The floor of 1.31–1.80% assumes the plaintext's adjacent-difference distribution resembles English rune text. Two cases could slip under it: a non-English plaintext, or a key correlated with word-position classes, which are visible in the ciphertext. Neither was checked.

---

## 2. IoC ≈ 1.0, flat frequency and word lengths: which cipher classes fit?

### Takeaway
Every unsolved section has normalised IoC between 0.981 and 1.004, and the unigram distribution is indistinguishable from uniform (χ² p = 0.55). No periodic IoC peak appears up to period 40. Only non-periodic polyalphabetic systems fit: running key, OTP/PRNG stream, prime-type or other aperiodic sequences, chain or ciphertext-feedback ciphers, or a periodic key longer than a page. Word lengths are preserved (separators are in clear), but the distribution is **not** English-like. There are too few 2-rune words (15.5% vs 22–24%) and too many long words.

### Cited Findings
- [MEASURED-LOCAL] Normalised IoC per section: 0.988, 1.004, 0.999, 1.001, 0.994, 0.991, 0.996, 1.002, 0.981. Pooled: 0.9999. Unigram χ² vs uniform: 26.4 on df 28, p = 0.55. For comparison, the solved English or near-plaintext sections have IoC 1.52–1.91; Vigenère-DIVINITY 0_welcome has 1.17 and p56 totient stream has 0.94. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] The maximum periodic IoC for periods 1–40 is ≤ 1.09 in every large section, with the peaks at scattered long periods (24, 35, 40, …), which is consistent with noise. p54-55 reaches 1.21 at p=26, but it has only 308 runes, so its columns hold about 12 runes. The delta stream Δ ∈ 1..28 has IoC 1.008–1.035 against 29/28 = 1.036 for uniform on 28 symbols, also with no periodic peak. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] Repeated n-grams match a random text: distinct repeated 4-grams 127 (≈119 expected), 5-grams 6 (≈4.1), 6-grams 1 (≈0.14), 7-grams 0. No word of 4 or more runes repeats anywhere in the unsolved pages. English with a per-word or periodic key would repeat words such as THE, THAT and WITH. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [REPORTED] "No periodicity, no Kasiski signal, and no keystream shared between sections." — [Leo-Y-Zhang/LiberPrimusAnalysis](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis); "Positional IoC: flat" — [RiskAverseTech STATUS.md](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md); "IoC·N 1.000" — [Dukotah](https://github.com/Dukotah/cicada3301)
- [REPORTED] A search snippet of swarmpool.org: IoC "sits exactly at random uniform baseline — consistent with key length ≫ page length, or a non-Vigenère cipher entirely." — [swarmpool.org](https://swarmpool.org/)
- [REPORTED] Background: autokey extends a short primer with plaintext or ciphertext, while a running key comes from a long external text. Ciphertext autokey is easier to break than plaintext autokey. — [Pommerening, Univ. Mainz: Autokey](https://www.staff.uni-mainz.de/pommeren/Cryptology/Classic/7_Aperiodic/Autokey.html) (search snippet)

**Word lengths**
- [MEASURED-LOCAL] Rune-count word lengths, with words wrapping across line breaks joined. Unsolved (2,900 words): 1 rune 3.0%, 2 runes 15.5%, 3 runes 24.8%, 4 runes 17.6%, 5 runes 10.9%, 6 runes 8.8%, 7 runes 7.4%, 8 runes 5.4%, ≥9 runes 6.4%. English prose (25,812 words): 6.1, 21.8, 22.2, 18.9, 9.7, 8.3, 5.9, 3.3, 3.9. LP solved plaintext (740 words): 3.8, 24.1, 23.6, 17.7, 7.7, 8.8, 6.4, 3.4, 4.6. The unsolved distribution differs from both: χ² = 213 (p ≈ 1e−41) and χ² = 195 (p ≈ 7e−38), df 8. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] Caveat: if line breaks are instead treated as word breaks, 1-rune words jump to 9.7% and 2-rune words to 18.8%. The word statistics therefore depend on transcription conventions for words that wrap across lines. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [REPORTED] "Two-rune words: 15.9% vs 24–25% in English; chi-square 183, p 0.0005" and "Fitted filler rate: 0.40 per word". The plain decoder's power at that filler rate is 0.02. — [RiskAverseTech STATUS.md](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md)
- [MEASURED-LOCAL] Single-rune words in the unsolved text are spread over many runes: T 19, U 18, EA 17, NG 17, P 17, D 17, … In English they would be almost only A and I. So the key varies from position to position, not per word. — [relikd transcription](https://github.com/relikd/LiberPrayground)

### Inferences
- Flat IoC, flat unigrams, no Kasiski repeats and no repeated words together rule out per-word keys, short periodic keys and simple or homophonic substitution. Each remaining class (running key, OTP/PRNG, aperiodic integer sequences, chain or feedback ciphers, multiple encryption with a long effective key) produces IoC ≈ 1 by itself. Only the doublet deficit separates them, and it selects the ciphertext-feedback variants.
- The word-length mismatch has several candidate explanations: (a) null or filler runes inserted, as in RiskAverseTech's fitted model; (b) separators that do not mark true plaintext word boundaries; (c) a different language, register or spelling convention, such as heavy use of digraph runes; (d) transcription choices on line wraps. Whichever applies affects any word-anchored crib attack. Fewer short words also means fewer cribs for THE, OF, TO and A.

### Gaps
- I found no independent word-length analysis on the wiki or Reddit to cross-check RiskAverseTech's 15.9% against my 15.5%. The small difference probably comes from the transcription or the treatment of line wraps.
- I measured no per-section word-length variation and no rune-at-word-start statistics beyond F: the word-initial F rate is 3.9% vs 3.5% overall.

---

## 3. Other measured anomalies: F runes, gematria sums, positional effects, repeats, first and last words

### Takeaway
Apart from the doublet deficit, the reported anomalies are weak, contested or already explained. They include lag-5/lag-6 "echoes", an excess of S pairs, a line-initial IoC bump attributed to typesetting, and a single repeated 6-gram at the very end of the corpus. F frequency (3.5%) shows no interrupter excess that the ciphertext alone can detect.

### Cited Findings
- [MEASURED-LOCAL] F (ᚠ, index 0) makes up 458/12,956 = 3.54% of runes, against 1/29 = 3.45% expected. Per section it ranges from 1.95% (p54-55) to 4.66% (p0-2). Word-initial F: 3.9% of words. There are 4 F-F doublets. No ciphertext-only F excess was found that would mark plaintext F interrupters. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] There is exactly one repeated 6-gram, D-J-U-B-E-I. It occurs at global rune offsets 6,555 (p27-32, about the 28th rune) and 12,950, the last 6 runes of the whole unsolved corpus (end of p54-55). The gap is 6,395. Expected repeated 6-grams ≈ 0.14, so P(≥1) ≈ 13%: weak on its own, but the position at the very end is curious. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [REPORTED] RiskAverseTech lists further anomalies, numbered by section of their STATUS.md:
  - "Lag-5 equality: 102 pairs vs 71 expected." Family-wise p 0.015.
  - "Lag-6 relation c = 24 − 2c′: 77 hits vs 44 expected." Family-wise p 0.008 over 5,684 cells.
  - "S pairs: 11 observed. Expected 3.5 under a uniform key (p 0.005) and about 6.5 under an English running key." S concentration family-wise p 0.085; the §82 criterion failed and the S carrier is treated as open.
  - "Line-initial column 0 pooled z +7.2", explained by "line fill selecting wide glyphs", i.e. typesetting, and closed.
  - "Lag-6 hits in words of 10+ runes: 30 vs 59 ± 9."
  - Their best descriptive model, "E56w+n" (echo plus filler), "is a description, not a decryption" and predicts 5 S pairs against the 11 observed.

  These "lag-5 equality" counts evidently use a restricted definition, perhaps within-word or by a specific pair class. My unrestricted lag-5 coincidence is 3.70%, about 479 pairs, which is not significant. — [RiskAverseTech STATUS.md](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md)
- [REPORTED] Dukotah's transcription caveat: "The pooled LP1+LP2 read gate failed (95.09% vs 99%), so the transcription claim is limited to LP2 typeface." Pages 49–51 have canonical-byte disputes, with an owner decision recorded 2026-10-29. — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)

### Inferences
- The lag-5/lag-6 echoes and the S-pair excess are the only candidate secondary signals in the public record. Their family-wise p-values sit around 0.01, after very large searches, and the repository that found them withdrew or qualified several of its own claims. They deserve one independent replication, not heavy investment.
- If F were a plaintext interrupter left unencrypted with the key not advanced, as in the solved pages, F frequency would be inflated by roughly the plaintext F rate (2–3% of English rune text) on top of 1/29. That would give about 5–6%. The observed 3.5% argues against unencrypted F interrupters at English frequency in the unsolved pages. This is my own inference; I found no source that quantifies it.

### Gaps
- I could not reach any source on line- or page-level gematria sums for the unsolved pages, or on the patterns of first and last words. I did not compute gematria sums.
- I found no community analysis of the D-J-U-B-E-I repeat.

---

## 4. Which hypotheses are already ruled out, and on what evidence

### Takeaway
On ciphertext statistics alone, the following are ruled out: simple and homophonic substitution, short-period Vigenère or Beaufort with or without F-interrupters, per-word keys, pure ciphertext autokey, and any additive or affine cipher with a key independent of the plaintext. That includes English running keys, OTPs, primes, totients and PRNGs without a feedback or rejection rule. Many labs have additionally excluded specific keys by exhaustive search, but those exclusions apply only to the exact constructions searched.

### Cited Findings
- [MEASURED-LOCAL] Simple, homophonic or monoalphabetic substitution is ruled out: such ciphers preserve plaintext IoC (≈1.5–1.9 for LP plaintext), while the unsolved IoC is 0.98–1.00. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] Periodic polyalphabetic keys with period ≤ 40 are ruled out: no periodic IoC peak (max ≤ 1.09 in large sections), and n-gram repeats sit at random expectation. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [MEASURED-LOCAL] Plaintext-independent additive or affine keys are ruled out by the doublet floor of ≥1.31–1.80% against 0.66% observed (Section 1). This covers the Vigenère, Beaufort, running-key, totient-prime, OTP and PRNG families **unless** a feedback or rejection rule is added. — [relikd transcription](https://github.com/relikd/LiberPrayground)
- [REPORTED] Leo-Y-Zhang excludes periodic keys (with and without F-interrupt and key-skip), 46 integer sequences in raw and chain form, autokeys and prime-value feedback, running keys from Cicada-linked texts, shared keys between sections, digraphic ciphers, and "Vigenère, Beaufort, running key, atbash, totient stream, autokey". He also excludes outguess payloads from all 75 page images (no key and 96 keys) and matches the page-56 SHA-512 against 697,000 candidates with no hit. — [Leo-Y-Zhang/LiberPrimusAnalysis](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis)
- [REPORTED] RiskAverseTech: about 1.24 billion pre-registered decoder tests with planted controls, and 46 of 76 lanes closed null. Their exclusions:
  - external running keys at every offset (153 M tests, 12 texts);
  - seeded PRNGs (8 generators × 2^18 seeds);
  - keyword-mixed alphabets (25.6 M tests);
  - Cicada's own words as keys;
  - irrational digits (6.5 M tests);
  - stream keys at cumulative page offsets (145 M tests);
  - "English running keys as a class … Closed for rune-consumed keys with English on both sides";
  - key reuse between pages, "clusters under ~12 pages not excluded".

  Their own §47 exclusion of every plaintext-independent key was later withdrawn. — [RiskAverseTech STATUS.md](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md)
- [REPORTED] Dukotah: autokey "positively refuted"; a keytext class of about 200 texts closed under both skip and rewrite constructions. A public-pad sweep found 0 hits in about 14.5×10⁹ offsets over Bitcoin heights, the NIST Beacon, RANDOM.ORG, RAND digits and 3301's published bytes; this is "narrowed, not closed". The Python 2.7 Mersenne Twister full 2³² seed space is null under the "pair" relation only, and the exact/keyskip1 sweep was 44% complete when it stopped. Bash `$RANDOM` and PHP `mt_rand` were screened negative. Caveat: "every negative is English-register", and the scorer had power 0.33 for Latin and 0.00 for Welsh. — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)
- [REPORTED] Dukotah's verdict: "OTP-class", meaning the ciphertext cannot separate a true pad from a seed-derived keystream (6-statistic battery against SHA-256-CTR, max |z| = 1.60). "Unsolvable-by-design" was narrowed on 2026-08-17. — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)

### Inferences
- The statistical exclusions (substitution, short-period keys, plaintext-independent additive keys) are robust and need no further search effort.
- The exhaustive-search exclusions are construction-specific. Many were run without the re-draw/skip rule that the doublet data demand, or with only one variant of it. A key family "excluded" under plain Vigenère is **not** excluded under "Vigenère plus skip-if-same" or under chain encoding. That is where the gap lies.
- Most labs scored only English plaintext. Dukotah reports near-zero scorer power for Latin and Welsh. Non-English or Old English plaintext under the right mechanism would have been missed.

### Gaps
- I found no independent replication of the large search claims of RiskAverseTech, Leo-Y-Zhang or Dukotah. All of them date from 2026, and none is peer-reviewed.
- I found no consolidated list of which key families were tested *in chain form plus skip-rule form plus non-English scoring* together.

---

## 5. Ranked, concrete hypotheses for a search lab

### Takeaway
The doublet constraint narrows the space more than any other statistic. Searches should be built on mechanisms that look at the previous ciphertext rune, with positive controls made by re-encrypting the solved pages under each mechanism. The ranking below weighs consistency with the measurements, cost, and how much prior search left the hypothesis open.

### Cited Findings
- [REPORTED] Only the chain cipher reproduces the fingerprint among the families Leo-Y-Zhang tested: "Only a chain cipher … reproduces the observed fingerprint" — [Leo-Y-Zhang](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis). A soft re-draw survives in RiskAverseTech's tests — [RiskAverseTech](https://raw.githubusercontent.com/RiskAverseTech/cicada-ioc/main/STATUS.md). Dukotah reports an anti-repeat filter with p_keep ≈ 0.18 as machine-applied — [Dukotah](https://github.com/Dukotah/cicada3301).
- [MEASURED-LOCAL] Simulations: chain cipher 0.00% doublets and skip-if-same 0.00%. Every plaintext-independent key gives ≥1.3% (floor) or about 3.4% (typical). — [relikd transcription](https://github.com/relikd/LiberPrayground)

### Inferences: ranked list

**H1. Delta-stream reformulation (chain or ciphertext-feedback cipher).** This is cheap and has the highest prior.
- Transform the ciphertext to s[i] = (c[i] − c[i−1]) mod 29. Map {1..28} → {0..27}, and also try the reverse sign, so the stream lives in Z28.
- Run the full existing attack battery on s in Z28 *and* Z29 arithmetic: known LP keys (DIVINITY, FIRFUMFERENFE, …), the totient-prime and prime streams used on p56, Atbash and shift, affine, periodic up to 100, and running keys from the solved LP plaintext and Cicada texts.
- Also try s[i] = (p[i] + k[i]) mod 28 + 1 and s[i] = (p[i] + k[i]) with 0 → re-draw.
- Leo-Y-Zhang reports testing 46 integer sequences in chain form. Keyword and periodic keys, LP-text running keys and non-English scoring in the delta domain appear untested in the sources I found.
- Positive control: chain-encrypt the solved pages and recover them.
- Pass/fail: an n-gram score z above the planted-control bar on any section.

**H2. Vigenère or stream cipher with a probabilistic or conditional skip-if-same (re-draw) rule.** The rule fires with probability about 0.81, or under a hidden condition.
- Decode with a small HMM or Viterbi lattice over "key index advanced by 0, 1 or 2" states. Use the emission constraint that a skip is only possible where p + k[j] = c[i−1].
- Candidate streams: totient-prime (as on p56), primes, Fibonacci, π/e/φ digits, the LP solved plaintext as a running key, the DIVINITY and FIRFUMFERENFE periodic keys.
- Fit the trigger probability: 0.81 is the target. Also test deterministic triggers that would explain the 19% failures, such as the rule being checked in Latin-letter space, against the rune two places back, or only when k[j] is non-zero.
- Dukotah closed about 200 keytexts under skip and rewrite. Most integer-sequence and periodic families under the soft rule appear untested.

**H3. Deconvolution test (cheap exclusion experiment).**
- Compute the Δk distribution a plaintext-independent additive key would need: deconvolve the observed Δc histogram by the English Δp histogram over Z29 using the DFT.
- If no non-negative solution exists, which the min-floor bound in Section 1 predicts, the "independent key" class is formally closed for every plaintext corpus tested. Repeat with Latin, Old English and Welsh rune corpora to close the non-English loophole.
- Also test key-depends-on-word-position classes: compute the floor per (position-in-word, boundary) class.

**H4. Filler or null-rune hypothesis for the word-length anomaly.**
- Fit models in which nulls are inserted at rate λ per word, or separators are dropped or added. Use the English length distribution to match the observed 2-rune deficit (15.5% vs 22–24%) and long-word excess.
- RiskAverseTech fitted λ ≈ 0.40 per word.
- Combine with H1 and H2: a cipher that inserts a random rune whenever a doublet would appear would explain *both* the doublet deficit and longer words. Test whether the excess length per word (≈0.3–0.4 runes) is the right size to come from doublet-avoidance insertions. A rough check: about 3.4% of positions, about 0.13 runes per word, which looks too small by itself. That deserves a careful calculation.

**H5. The D-J-U-B-E-I repeat and depth at offset 6,395.**
- Test for key reuse: run a depth test (lag-6395 coincidence and Δ-coincidence) in a window around the alignment of global offsets 6,555 and 12,950. Do it under raw, chain (Δ) and skip-adjusted alignments.
- This is cheap, with a low prior (p ≈ 0.13 that the repeat is chance).

**H6. Replicate the lag-5/lag-6 "echo" and S-pair anomalies** (RiskAverseTech §42, §46, §80) on this lab's transcription with a pre-registered definition. If they replicate, they are a second constraint on the mechanism, for example a feedback tap at lag 5 or 6, as in c[i] = p[i] + k[i] + c[i−5]. This is cheap.

**H7. Seed-derived PRNG with a rejection rule** (e.g. `while c == prev: k = rand()`).
- Typical 2014-era implementations: Python 2.7 `random`, PHP `mt_rand`, bash `$RANDOM`, C `rand()`/glibc, Java LCG.
- Re-run the seed sweeps *with the rejection loop consuming extra PRNG outputs*. That changes key alignment after every rejection, which plain-stream sweeps miss.
- Dukotah's Mersenne Twister sweep was null only under the "pair" relation, and his exact/keyskip1 sweep stopped at 44%.
- Expensive (2³² seeds per generator) but well defined. Run it after H1–H3.

**H8. Non-English plaintext under H1 and H2.** Re-score H1 and H2 outputs with Latin, Old English and Welsh rune n-gram models; the 12-register idea comes from Dukotah. Do it only after H1 and H2 are implemented. The marginal cost is low.

**Housekeeping for this lab** (not a hypothesis): fix the `src/lplab/stats.py` module docstring. It says the anomaly comes from "a key that never repeats a shift of 0 with respect to the previous character". Simulation shows such a key gives 3.44% doublets, i.e. no suppression. The constraint is on the *ciphertext*: c[i] ≠ c[i−1] about 81% of the time.

### Gaps
- No source quantifies how many of the families excluded under plain Vigenère have been re-tested under H1 or H2. The ranking assumes most have not.
- The re-draw trigger probability of 0.81 has been fitted by two labs, but no source explains *why* about 19% of doublets would survive under a deterministic computer implementation. This is open.

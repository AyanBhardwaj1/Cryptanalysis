# Liber Primus: solve history, community attacks on the unsolved pages, Cicada's hints, and community resources

Research date: 2026-11-10. Network note: uncovering-cicada.fandom.com, web.archive.org, relikd.github.io, connortumbleson.com, cicada3301.boards.net and Reddit mirrors could not be reached from this session (DNS/proxy block). Wiki content below is cited only where a reachable primary source quotes it, and is flagged as such. Most sources are GitHub repositories (primary code and data). The 2026 "lab" repositories are self-published and AI-assisted, and none is peer-reviewed. Their negatives are self-reported. Each shows planted-key controls, but I did not re-run them.

Numbering conventions differ, so check them before you compare results:
- **LP1** (2014 onions 3-6) is jpgs 00-16 plus 107.jpg, 167.jpg and 229.jpg.
- **LP2** (Onion 7) is 0.jpg-57.jpg. The unsolved pages are LP2 0-55, and pages 56-57 are solved.
- rtkd/iddqd numbers the whole book as 74-75 pages: unsolved LP2-00..55 = master chunks 16..71 = images 17..72. The rtkd index counts one extra leading page — [cicada-ioc SOURCES.md](https://github.com/RiskAverseTech/cicada-ioc/blob/main/SOURCES.md); [scream314 pages_and_ciphers.md](https://github.com/scream314/cicada3301/blob/master/pages_and_ciphers.md)

## Q1. Which sections are solved, with what cipher, key and interrupters? Any later partial solves or credible claims (2016-2026)?

### Takeaway
Nine sections are solved, all in 2014-era material. They use four ciphers:
- plain Gematria (no encryption);
- Atbash, plus Atbash with a shift of 3;
- Vigenère with the keys DIVINITY and FIRFUMFERENFE;
- a stream that subtracts φ(prime_n) = p_n − 1.

Every keyed section uses the same "interrupter" rule: a plaintext F is written as ᚠ unencrypted and consumes no key. No credible partial solve of LP2 pages 0-55 has been published from 2016 to November 2026. Every 2026 lab I found states explicitly that nothing in LP2 is solved.

### Cited Findings
**Canonical key table (rtkd/iddqd keys file)**
- 0.0 Atbash ("Substitution. Invert Gematria").
- 0.1 "Polyalphabetic Substitution. Clear text F is not encrypted. Key: divinity (23,10,1,10,9,10,16,26)".
- 0.2 and 0.4 "Substitution" (plain Gematria).
- 0.3 "Substitution. Invert Gematria. Key: 3".
- 0.5 "Polyalphabetic … Clear text F is not encrypted. Key: firfumferenfe (0,10,4,0,1,19,0,18,4,18,9,0,18)".
- 0.6 plain; 0.7-0.15 "-" (unsolved).
- 0.16 "Polyalphabetic … Clear text F is not encrypted. Key: f(n)=phi(n) where n = stream of prime numbers".
- 0.17 plain.
- Source: [rtkd/iddqd liber-primus__keys.txt](https://github.com/rtkd/iddqd/blob/f2267b0c2f1e1d2662806b90b9c3a2953b3a7023/liber-primus__keys/liber-primus__keys.txt)

**Per-section mapping, cross-verified rune for rune against rtkd's translation** — [cicada-ioc SOURCES.md](https://github.com/RiskAverseTech/cicada-ioc/blob/main/SOURCES.md):

| Master chunk(s) | Section | Rule |
|---|---|---|
| 1 | A Warning | Atbash, p = 28 − c |
| 2-3 | Welcome | Vigenère DIVINITY (23 10 1 10 9 10 16 26), with the F rule |
| 4 | Some Wisdom | plain |
| 5-8 | A Koan / An Instruction | shift 3 then Atbash, p = 2 − c mod 29 |
| 9-12 | Loss of Divinity / Some Wisdom / An Instruction | plain |
| 13-14 | A Koan (circumference) | Vigenère FIRFUMFERENFE, with the F rule |
| 15 | An Instruction / Know This | plain |
| 72 | An End | subtract φ(p_n) = p_n − 1 over the primes, with the F rule |
| 73 | Parable | plain |

- The only differences in that check were the book's own "WIDSOM" misspelling, a "FOLLWING" typo in the translation file, and the untranslated "Know This" list.

**Exact interrupter positions (relikd/LiberPrayground `solver.py`)** — [LiberPrayground solver.py](https://github.com/relikd/LiberPrayground/blob/master/solver.py)
- Welcome: `KEY_DATA=[23,10,1,10,9,10,16,26] # DIVINITY`, `INTERRUPT='ᚠ'`, `INTERRUPT_POS=[4,5,6,7,10,11,14,18,20,21,25]`. These are 1-based occurrences of ᚠ.
- Koan 1: `inpt.invert()` then key `[26] # Y`.
- jpg107-167: FIRFUMFERENFE, `INTERRUPT_POS=[2,3]`.
- p56 An End: `FN = lambda i, r: r - (PRIMES[i] - 1)`, `INTERRUPT_POS=[4]`.
- Warning: invert. Wisdom, Loss of Divinity, jpg229 and Parable: plain.

**Interrupt semantics (LiberPrayground README)**
- "the solution to jpg 107–167 skips the F rune at position 49 and 58 (ignoring whitespace)".
- `kj 2,3` sets these by nth occurrence. The first occurrence is index 1.
- Source: [LiberPrayground README](https://github.com/relikd/LiberPrayground)

**Page map (scream314)** — [scream314 pages_and_ciphers.md](https://github.com/scream314/cicada3301/blob/master/pages_and_ciphers.md)
- 00.jpg: English title.
- 01.jpg: A Warning, "Substitution with reversed Gematria".
- 02.jpg: "Intus", Chapter 1.
- 03-04.jpg: Welcome. Key written as the shifts 6,19,28,19,20,19,13,3 "shift up", which is 29 − DIVINITY.
- 05.jpg: Some Wisdom, plain.
- 06-09.jpg: Koan, "Shift 3 down reversed Gematria".
- 10-13.jpg: Loss of Divinity, plain.
- 14-15.jpg = 107/167.jpg: Koan 2, FIRFUMFERENFE.
- 16.jpg = 229.jpg: An Instruction, plain.
- LP2 0-55: "?" (unsolved).
- 56.jpg: "nth letter's shift = phi(nth prime) % 29. Shift down forward Gematria", with the F note.
- 57.jpg: Parable, plain.

**Key origins**
- FIRFUMFERENFE is CIRCUMFERENCE with each C replaced by F. The LiberPrayground "d" (decrypt) example shows the substitution needed for "A KOAN" is "F IRFU". The key words come from solved text ("the I is the voice of the circumference", "the loss of divinity") — [LiberPrayground README](https://github.com/relikd/LiberPrayground); plaintexts in [LiberPrayground pages](https://github.com/relikd/LiberPrayground/tree/master/pages)

**Solved plaintexts that matter for keys and hints** (transliterated from the solved page files that came from LiberPrayground) — [LiberPrayground pages](https://github.com/relikd/LiberPrayground/tree/master/pages)
- Some Wisdom: "THE PRIMES ARE SACRED. THE TOTIENT FUNCTION IS SACRED. ALL THINGS SHOULD BE ENCRYPTED. KNOW THIS:" followed by a 5×5 square mixing numbers and rune words: 272 138 SHADOWS 131 151 / AETHEREAL BUFFERS VOID CARNAL 18 / 226 OBSCURA FORM 245 MOBIUS / 18 ANALOG VOID MOURNFUL AETHEREAL / 151 131 CABAL 138 272.
- An Instruction (229.jpg): "QUESTION ALL THINGS. DISCOVER TRUTH INSIDE YOURSELF. FOLLOW YOUR TRUTH. IMPOSE NOTHING ON OTHERS. KNOW THIS:" followed by the 5×5 square 434 1311 312 278 966 / 204 812 934 280 1071 / 626 620 809 620 626 / ….
- An End (p56): "WITHIN THE DEEP WEB, THERE EXISTS A PAGE THAT HASHES TO 36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a8425893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4. IT IS THE DUTY OF EVERY PILGRIM TO SEEK OUT THIS PAGE." The hash is 128 hex characters (512 bits).
- Parable (p57): "LIKE THE INSTAR TUNNELING TO THE SURFACE. WE MUST SHED OUR OWN CIRCUMFERENCES. FIND THE DIVINITY WITHIN AND EMERGE."
- Loss of Divinity ends: "…THAT HAVE US LOSE OUR PRIMALITY, AND THUS OUR DIVINITY … AN INSTRUCTION: PROGRAM YOUR MIND. PROGRAM REALITY."

**Status in 2026: nothing in LP2 is solved**
- pnotisdev: "Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved." — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- cicada-ioc: "The unsolved pages are not readable English under any key or procedure this record or the other public ledgers have tried" (statement of 2026-11-01) — [cicada-ioc README](https://github.com/RiskAverseTech/cicada-ioc)
- Dukotah (status 2026-11-05): verdict "OTP-class, NOT 'unsolvable'" — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)

**Searches for 2025 solves**
- A search for 2025 solve claims found none credible. A December 2024 blog series covers re-extracting 2014 puzzle stages, not decrypting new LP pages (search snippet only; the host was blocked) — [connortumbleson.com 2024-12-23](https://connortumbleson.com/2024/12/23/the-cicada-3301-mystery-puzzle-3-solve-part-4/)

**A disagreeing description of the solved pages**
- jbo's cicada_tools describes the solved sections with some different emphases. Its README calls "A Warning" an Atbash-like linear shift, and it lists "DIVINITY", "CIRCUMFERENCE" and CONSUMPTION/PRESERVATION/ADHERENCE as keywords that appear on the solved pages — [yo-yo-yo-jbo/cicada_tools](https://github.com/yo-yo-yo-jbo/cicada_tools)

### Inferences
- The four solved keyed constructions share three properties:
  - additive mod 29 over Gematria index order (F=0 … EA=28);
  - decryption by subtraction, p = c − k;
  - the plaintext-F interrupter, where the key does not advance at an unencrypted ᚠ.
- Every key is either a word from the book's own text with a spelling twist (C→F) or a "sacred" number stream (φ of primes). The unsolved section should share this "house style" unless the author changed method for LP2, and the LP2 statistics in Q2 show that LP2 does not match the solved pages' single-layer additive pattern.
- The interrupter positions are not derivable from the ciphertext alone: they were found by trial or by crib. A lab therefore needs a search over skip sets; LiberPrayground's InterruptSearch does this with sequential and genetic search.

### Gaps
- I could not confirm exact solve dates or solver handles for each section, because the Uncovering Cicada wiki "How the solved pages of the Liber Primus were solved" page is blocked here. From memory and unverified: Warning and Welcome were solved within days of release in 2014, and An End was solved in 2014.
- I did not verify whether the An End hash is SHA-512 or another 512-bit hash. The community generally assumes SHA-512 or a similar 512-bit hash (unverified). The page has never been found.

## Q2. What has publicly been tried on the unsolved pages (LP2 0-55), and what has been ruled out?

### Takeaway
The single strongest constraint is the doublet deficit. Community members documented it around 2014 on the wiki's Ideas page, and three or more independent 2026 labs have replicated it: LP2 has 86 adjacent equal runes where about 445 are expected (0.66% against 3.45%).

**What the deficit rules out:** any cipher whose keystream is independent and uniformly differenced. That covers:
- plain Vigenère and Beaufort;
- running keys from books;
- prime or totient streams;
- OEIS sequences and PRNG streams applied additively.

**What the deficit allows:** a mechanism that suppresses about 81% of would-be repeats. Examples are a key symbol redrawn or skipped when it would repeat the ciphertext, or a word-aware feedback cipher.

Within that frame, large sweeps have been run and are all null, under these exact settings:
- number-theory, OEIS, PRNG and book running keys;
- autokeys, periodic keys and transposition;
- the solved-text phrase keys.

The live frontier is:
- "filler-aware" or insertion-aware decoders;
- anti-repeat decoders with key material that is not public;
- the "their numbers are the direction" pointer rules.

### Cited Findings

**Statistical facts about LP2 (the constraints any candidate must reproduce)**
- **Size and flatness:** 12,956 runes; IoC·N 1.000 (random 1.000); entropy 4.857 bits against a 4.858 maximum; doublet rate 0.66-0.68% against 3.45% random. Dukotah models this as a soft anti-repeat filter (about 83% suppression, p_keep ≈ 0.18) — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)
- **The doublet deficit is cipher structure, not plaintext structure.**
  - Solved plaintext has 77/2,968 doublets (0.0259). Solved ciphertext has 75/2,960. Unsolved ciphertext has 86/12,901 (0.0067, z −17.3 against uniform).
  - The deficit is the same inside words (0.0062) and across separators (0.0080).
  - The solved encrypted pages sit at the uniform rate (z −1.6 to −0.1).
  - Source: [cicada-ioc README §4](https://github.com/RiskAverseTech/cicada-ioc)
- **Which constructions reproduce the doublet count** (20 constructions, 200 replicates each, scored on doublets, lag-1 difference-class chi², unigram chi² and IoC) — [cicada-ioc README §5](https://github.com/RiskAverseTech/cicada-ioc)
  - Ruled out, at 430-506 doublets: independent uniform keys, English running keys, a hand pad with no repeated key symbol, and the book's own Vigenère and totient streams.
  - Ruled out: plaintext autokey at lags 1-5 (481-698 doublets).
  - Ruled out: ciphertext autokey at lags 1-5 (207-445).
  - Ruled out: ciphertext feedback tuned so a doublet means EA. It matches the count, but its lag-1 chi² is 9,629 against 42.
  - Ruled out: Vigenère that steps its key on a doublet (15 doublets).
  - Ruled out: "+1 when a doublet would form" at 81%. It matches the count, but its chi² is 299.
  - Ruled out: a hard redraw rule (0 doublets).
  - The only fit: a "uniform key re-drawn when it would repeat, ~81% of the time" (87 ± 10 doublets, consistent on all four statistics).
- **Prior community work, as cited by cicada-ioc §11** (I could not fetch these pages directly) — [cicada-ioc README §11](https://github.com/RiskAverseTech/cicada-ioc)
  - The Uncovering Cicada wiki "Liber Primus Ideas and Suggestions" page already reported 86 same-rune pairs in about 13,000 runes. It called this "the only solid clue towards cipher/key found in runes" and proposed algorithms using the previous rune's value, or a key that "jumps to the (n+1)th number in the stream key".
  - The wiki's "Frequency Analysis Unsolved Pages" page has per-chapter doublet tables.
  - jens-wedin/liber-primus independently finds p_keep ≈ 0.19 with uniform collision resolution.
  - wazar/cicada3301 independently finds ≈83% suppression.
  - Leo-Y-Zhang/LiberPrimusAnalysis reports 86 against 447 and excludes periodic keys (with and without the F and key-skip rules), integer sequences, autokeys, prime-value feedback, running keys and shared keys between sections.
- **Other positive signals (pnotisdev)** — [pnotisdev FINDINGS.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/FINDINGS.md)
  - A lag-6 relation inside words, c′ = 24 − 2c mod 29: 80 against 44.5 expected, z +5.3, none across word gaps.
  - A lag-5 "S" echo, later dropped as a selection effect (P 0.021).
  - Too few 2-rune words: 15.5% against 20-27%. The best fit is one extra rune in about 42-45% of words.
  - "DJU BEI" is the only repeated adjacent word pair, and its second copy is the book's last two words.
  - All other n-gram and lag statistics are flat.
- **cicada-ioc's version of the echo signals** — [cicada-ioc README §0](https://github.com/RiskAverseTech/cicada-ioc)
  - Lag-6 at 77 against 44.
  - A lag-5 equality excess of 102 against 71, which survives.
  - The S weighting of lag 5 is not significant (p 0.085).
  - The two sources differ on whether lag 5 survives.
- **Two verifiers for any claimed decryption** — [pnotisdev FINDINGS.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/FINDINGS.md)
  - In solved pages every one-rune word decrypts to A or I (27/27). LP2 has 83 one-rune words.
  - 36 of 76 solved clauses have prime Gematria sums (z 7.9). The ID3 tag of a 2013 Cicada audio file carries the Parable text and 1,595,277,641 = 1259 × 1031 × 1229, the product of its prime clause sums.
- **A quick falsification test for proposed ciphers** — [pnotisdev FINDINGS.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/FINDINGS.md)
  - 23 of LP2's 86 doublets cross word gaps, which uniform placement predicts.
  - So a cipher that can make a doublet only on one plaintext rune is excluded.
  - On this test, a Discord-proposed "cumulative prime cipher" (handle avaster) and "book + random skip" (handle DCPH) were excluded.
- **Doublets and IoC as a digraph argument (jbo)** — [yo-yo-yo-jbo/cicada_tools](https://github.com/yo-yo-yo-jbo/cicada_tools)
  - jbo's README argues that the rare doublets suggest Playfair-like handling, and that IoC tests suggest the cipher works on two letters at once.
  - This is an opinion, and the flat-bigram results above contradict it: pnotisdev says "unigrams, bigrams, every lag … all flat".

**Attacks run and reported null**

*Number streams, additive* — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- A 1,447-stream library (number theory, constants, Cicada numbers, hashes): 409 M decodes, 0 hits.
- The same library × all 28 multipliers: 5.7 bn decodes.
- Linear recurrences of order ≤ 3 and polynomials of degree ≤ 3: 9.2 bn decodes.
- 1,063 combined number-theory streams and functions at primes.
- Inverses, discrete logs and cubes mod primes.
- φ and σ of 3301i + 1033.
- Decimated library streams, word sums, and π, e, φ, √2 to 10^6.
- 199,088 OEIS sequences.

*LiberPrayground's own scripts* — [LiberPrayground README](https://github.com/relikd/LiberPrayground); [LiberPrayground solver.py](https://github.com/relikd/LiberPrayground/blob/master/solver.py)
- An OEIS checker over 294k sequences, first 40 terms, a 350k-word dictionary, offsets −1..+3, all 29 shifts, all F-interrupt combinations. No hits were reported.
- A totient playground with commented variants: r − p_i + z; Fibonacci-indexed primes; r.prime^i; sums of adjacent primes; and an elliptic curve (149, 263, mod 3299).
- An "n-gram shifter" in FailedAttempts.py.
- InterruptDB: the best IoC for the first 20 interrupts × all runes as interrupter × key length ≤ 32, about 1.36×10^10 operations.

*Classical structures* — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md); [pnotisdev FINDINGS.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/FINDINGS.md)
- Autokeys (lag ≤ 8), monoalphabetic, Vigenère to period 29 (periodic up to about 400 elsewhere), progressive, multiplicative and cumulative keys.
- Beaufort/Vigenère sign alternation (25 templates, best IoC 1.400).
- Ciphertext as key; key running backwards; ciphertext feedback c_i = a·c_(i−1) + p_i + k.
- Clocked key pointers (advance by 1 + index, prime, prime − 1); small state machines (4,608 rules × 29 states).
- Two-layer keyword Vigenère inside a number stream.
- Per-word keys (constant, linear, quadratic, periodic).
- Step-domain cipher (plaintext in c_i − c_(i−1)).
- "Transposition after encryption", plus reading-order transforms and 20 alphabet orders, including 15 OEIS prime orders.
- Ciphertext reversed per word, clause and line.

*Key restarts and key steps* — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- Restarts at every page, paragraph, line, sentence, word and clause mark, at the 10 red headings and 46 page starts, and mid-page sliding windows.
- Extra key steps at word, line and page boundaries.
- Keyless word-edge nulls.
- A "chanscreen v2" hold/spend/skip/coin channel likelihood search: 82 windows, 8.7 bn cells, 0 hits.

*Running keys and books*
- Book letters as a running key under the rune table or any untuned table: 17 texts, 6 languages. Excluded by flatness alone — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- A table-free book-key decoder on Liber AL (The Book of the Law), Blake × 2, Emerson (Self-Reliance), the Mabinogion, Agrippa 1651, Gibson's *Agrippa* and the KJV: 0 hits — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- Cited books as number streams (cumulative sums, word lengths) — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- 1,520 book-code pointer readings into 4 books — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- cicada-ioc's corpus adds The King in Yellow, the Kybalion, Bulfinch's *Age of Chivalry*, the Cypherpunk Manifesto, the Anglo-Saxon Rune Poem, Pilgrim's Progress and the Canterbury Tales, and Cicada's own signed messages from 2012-2017 — [cicada-ioc SOURCES.md](https://github.com/RiskAverseTech/cicada-ioc/blob/main/SOURCES.md)
- Dukotah: about 200 public texts swept "by exhaustion", with skip and rewrite constructions — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)

*PRNG and public pads*
- Ten generators over all 2^32 seeds.
- Epoch-second seeds for 2011-2015.
- Millisecond timestamps for 2012-2014 (Java, CPython, Ruby).
- Per-page and per-section seeds.
- 19.2 M passphrases and 719 k KDFs into hash streams.
- Hash streams of all 12,944 solved-text words and phrases (8.1 bn decodes).
- Source: [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- Dukotah adds the public-pad sweep — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301):
  - Bitcoin block heights 0-303,726;
  - the NIST Beacon from 2013-09-05;
  - 153 RANDOM.ORG daily archives;
  - RAND's A Million Random Digits;
  - 3301's own published bytes;
  - about 14.5×10^9 offsets, 0 hits.
- Dukotah also screened the Python 2.7 Mersenne Twister over all 2^32 seeds, plus Bash $RANDOM and PHP mt_rand.

*Solved-text keys and cribs*
- 1,940 solved-text keywords with Cicada's spellings, and φ(prime), under the "R4" repair/insertion mechanism: best −64 against a hit level of 29.8 — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- Solved-page words, phrases and lines as Vigenère keys with spelling variants: best 1.332 — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- Cribs: the DIVINITY WITHIN heading, title cribs — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- LP1 text as a running key — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- An r/cicada 2021 thread proposed using one LP page as the one-time pad for another. A reply reports trying "PRIMALITY" as a key with no luck (search snippet only; the host was blocked) — [r/cicada "Some notes on the unsolved pages" (2021)](https://red.ks32.dev/r/cicada/comments/nx5ls7/some_notes_on_the_unsolved_pages_of_the_liber)

*Key reuse between pages*
- Depth-two IoC test, pooled over all 1,485 page pairs: null for aligned reuse at any offset within ±200 runes and for any within-page period 2-200 — [cicada-ioc README Phase 1](https://github.com/RiskAverseTech/cicada-ioc)

*Puzzle furniture as keys* — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- The page-30 grid, the 1033 word square and the 3301 square were "explained puzzle furniture, not keys".
- The 256-byte payload is byte-random: no hash match and no decryption.
- No OutGuess payloads in any of the 56 LP2 scans.
- The signed 2014 payloads and hex blobs as keys: 272 streams, best 1.297.
- Cicada OS ISO files and audio as keys: uniformly random, 0 hits.
- An End's SHA-512 against 124,017 digests of archived onion captures: no match.

*Earlier and other community leads* — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- "Mike's period 13 on pages 54-55": P 0.26 after selection.
- "CicadaPG hash, page-55 affine, TRUTH overlay": not reproduced, or chance.
- The "community 464-word table": a selection effect.
- The Mayfly document's pixel-distance numerology (handle 7he5haman, 2020-21): its OEIS prime-permutation alphabet orders were screened, with no candidate — [pnotisdev SOURCES.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/SOURCES.md)

*Natural-numbers keystream*
- jbo's sample experiment: shift by index + start value 1..42, scored by F count — [yo-yo-yo-jbo/cicada_tools](https://github.com/yo-yo-yo-jbo/cicada_tools)

**What remains open (per the labs themselves)**
- **pnotisdev:**
  - The word-edge insertion campaign over all 82 windows is built but not run (about 300 CPU-hours; the one-window pilot was null).
  - Pointer direction by the words' numbers (18 conventions) and the remaining layout sign rules are queued.
  - "Not testable at LP2's size": two-tap echo rules, an evolving-alphabet walk, and key reuse between sections.
  - Its own estimate is about 50% that LP2's key cannot be recovered from the book alone.
  - Sources: [pnotisdev FINDINGS.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/FINDINGS.md); [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- **cicada-ioc:**
  - Most decoders (jens-wedin, wazar, Leo-Y-Zhang, Dukotah, farfromexact) model a key that may fail to advance. They have "no state for a page rune that consumed no key", meaning a filler or null insertion. The plain decoder has power 0.00 against one filler in ten.
  - About 85,000 keyless procedures were run, and none leaves LP2's footprints.
  - Its weight split: 40% "key material not public", 30% "an unenumerated process", 10% non-English plaintext, 10% images or page grid, 10% no message.
  - Sources: [cicada-ioc README §11, §0](https://github.com/RiskAverseTech/cicada-ioc)
- **Anglo-Saxon Rune Poem and GEB:** pnotisdev named the Rune Poem, RAND digits and Hofstadter's GEB (the 2014 onion-5 book-code source) but did not download them, and GEB is under copyright — [pnotisdev SOURCES.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/SOURCES.md). cicada-ioc did include the Rune Poem — [cicada-ioc SOURCES.md](https://github.com/RiskAverseTech/cicada-ioc/blob/main/SOURCES.md)

### Inferences
- **Fast filter for the lab:** every hypothesis must produce about 86 doublets in 12,956 runes, 23 of them across word gaps, with uniform lag-1 difference classes and flat unigrams. Any purely additive cipher with an independent key fails at 430+ doublets before decoding. Running such families "plain" — Vigenère, Beaufort, running key, totient or prime streams, OEIS, PRNG — is the most-repeated dead end. They are worth re-running only inside an anti-repeat (key-redraw or skip-on-collision) decoder.
- **The house-style mismatch matters:** the solved pages show no doublet deficit, so the LP2 mechanism differs from the solved pages' single-layer additive scheme. Reusing the solved ciphers' exact form (plaintext-F interrupters, one additive layer) is excluded. pnotisdev reports that "LP2 does not use the solved pages' literal-F rule in one layer".
- **Least-covered directions across the public ledgers:**
  - filler or insertion-aware decoding, where a rune consumes no key (word-edge and mid-word);
  - "numbers are the direction" pointer and sign rules driven by the word Gematria sums;
  - GEB, which is copyrighted and not swept by pnotisdev, as a key or pointer source;
  - two-layer schemes, for example anti-repeat over a keyword stream, beyond what pnotisdev and cicada-ioc ran;
  - non-English plaintext models (cicada-ioc ran Latin and Old English, so check its phase 5 before repeating).

### Gaps
- No source here gives a classic 2014-2019 community "What we have tried" list with specific keys (the wiki page is blocked). The pre-2020 Discord and IRC attempt record is mostly private or ephemeral.
- **Hill cipher and homophonic substitution:** I found no explicit public test. The flat unigram distribution over exactly 29 symbols and IoC·N ≈ 1.0 argue against simple homophonic schemes. I am inferring this; no source says it.
- **Magic-square-derived keys:** pnotisdev calls the squares "puzzle furniture, not keys", but I did not see the exact key derivations they tried (row or column reading orders, mod 29).
- The mortlach (2016-17) IoC and word-length analyses on cicada3301.boards.net could not be fetched. Only snippets were available: that IoC on early pages ruled out simple substitution, and that "word lengths [are] one of the biggest clues".

## Q3. What hints did Cicada give, and what outside-clue hypotheses are popular?

### Takeaway
Cicada's in-book hints are these:
- "The primes are sacred / The totient function is sacred / All things should be encrypted" (Some Wisdom).
- Two magic squares built from Gematria sums: sum 1033 in Some Wisdom, sum 3301 in An Instruction.
- An End's 512-bit hash of an unknown deep-web page.

The one post-2014 signed hint is the January 2016 message: "Liber Primus is the way. Its words are the map, their meaning is the road, and their numbers are the direction." It was followed in April 2017 by "Beware false paths. Always verify PGP signature from 7A35090F." Neither signed message contains key material.

### Cited Findings

**In-book hints**
- Some Wisdom (05.jpg) gives the three "sacred" lines. The KNOW THIS square's words are rune-sum stand-ins for the matrix found earlier in the 2014 Onion 3 out-of-band data (272 138 341 131 151 / 366 199 130 320 18 / 226 245 91 245 226 / …), "a magic square whose magic number is … 1033" — [scream314 2014.md](https://github.com/scream314/cicada3301/blob/master/2014.md); [scream314 liber_primus.md](https://github.com/scream314/cicada3301/blob/master/liber_primus.md)
- Gematria sums of the hint lines: "THE PRIMES ARE SACRED" = 853 and "THE TOTIENT FUNCTION IS SACRED" = 1039 — [scream314 liber_primus.md](https://github.com/scream314/cicada3301/blob/master/liber_primus.md)

**The 2014 puzzle chain that delivered LP (dates and mechanics)** — [scream314 2014.md](https://github.com/scream314/cicada3301/blob/master/2014.md)
- 2014-01-06: an image tweet. OutGuess revealed the signed poem "The work of a private man / who wished to transcend, / He trusted himself…" and a book code into Emerson's *Self-Reliance* (paragraph:sentence:word:letter) giving auqgnxjtvdbll3pv.onion. That onion's page was titled "For Every Thing That Lives Is Holy" (Blake).
- Onion 2: the comment "Patience is a virtue" (Gematria sum 761) and a 3.6 MB string that is three bit-inverted JPEGs. XORing their payloads gave a 14-column transposition: "ULTIMATE TRUTH IS THE ULTIMATE ILLUSION".
- Onion 3: the comment `<!--1033-->` and a 256-byte growing hex string. A leaked Apache server-status page revealed 05.jpg and the OOB magic square.
- Onion 5: the "Interconnectedness" mp3 (title sum 772, length 277.133 s) and the Goya portrait with a hidden "Rasputin" and number columns summing to 1033 and 3301. The portrait's OutGuess payload led to a GEB (Hofstadter) book code in chapter:line:word:letter format.
- Onion 6 (ut3qtzbrvs7dtvzp.onion): asked for three magic squares, which were hidden in the mp3 with OpenPuff, password 33011033. After submission it served 107.jpg, 167.jpg and 229.jpg.
- 2014-05-02: Cicada contacted registered hidden services with message.txt.asc. Its whitespace encodes the primes 2,3,5,7,11,13,17,23,29,31,37 (19 missing). It pointed to Onion 7 (ky2khlqdf7qdznac.onion), which served 0.jpg-57.jpg, i.e. LP2. The page title was "133", the div id "331", and Last-Modified was 2014-04-02 08:33:19 GMT.

**Signed messages after 2014** — [scream314 2016.md](https://github.com/scream314/cicada3301/blob/master/2016.md); [scream314 2017.md](https://github.com/scream314/cicada3301/blob/master/2017.md)
- 2016-01-05: OutGuess in the tweet image 4gq25.jpg, with the cicada logo and an "Oak Tree In Winter". The message reads: "The path lies empty; epiphany seeks the devoted. Liber Primus is the way. Its words are the map, their meaning is the road, and their numbers are the direction. Seek and you will be found. … Beware false paths. Verify OpenPGP 7A35090F." Signed 2016-01-01.
- 2017-04-04: signed "Beware false paths. Always verify PGP signature from 7A35090F." It was found on 2017-04-29 in #cicadasolvers, and its signature header reads "Version: CicadaPG v.3301".
- Both signatures verify against key 7A35090F (fingerprint 6D85 4CD7 9333 22A6 01C3 286D 181F 01E5 7A35 090F), and "neither contains a key" — [pnotisdev FINDINGS.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/FINDINGS.md)

**Hints never used** — [scream314 hints_never_used.md](https://github.com/scream314/cicada3301/blob/master/hints_never_used.md)
- The 2012 "P.S." 135-digit number, which rotated contains 3301/1033.
- The 2013 onion cookies 167= and 761= (SHA-256-like hex).
- "wisdom" and "folly" files in /tmp on the 2013 Cicada OS ISO.
- A 2013 telnet "primes" listing that omits every prime from 73 to 1223.
- Whitespace prime sequences in the 2012, 2013 and 2014 signed messages.

**Non-rune data inside LP2** — [scream314 pages_and_ciphers.md](https://github.com/scream314/cicada3301/blob/master/pages_and_ciphers.md); [scream314 liber_primus.md](https://github.com/scream314/cicada3301/blob/master/liber_primus.md)
- 32.jpg (LP2 page 15) has a 4×4 number grid: 3258 3222 3152 3038 / 3278 3299 3298 2838 / 3288 3294 3296 2472 / 4516 1206 708 1820.
- 49-51.jpg (book images 66-68) carry a "base60" two-character block (3N 3p 2l 36 …). scream314 notes one variant reading as "wrong!!!".
- pnotisdev treats the decoded 256-byte payload as byte-random and tested it as a key, with no result — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- OutGuess on most LP2 images yields only "garbage" (e.g. 58.2 kB) — [scream314 liber_primus.md](https://github.com/scream314/cicada3301/blob/master/liber_primus.md)

**Popular outside-clue hypotheses and their status**
- "Their numbers are the direction" as a key-pointer or sign rule:
  - 61 word-level sign rules: best 1.388.
  - Jump by word length: inside nulls.
  - LP2's own word sums as keys: nothing reaches 1.40.
  - Pointer direction by the words' numbers: only a pilot was run; the full run is queued.
  - Source: [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- cicada-ioc's guess: "the key moving by the words' numbers from a point not in the public record" — [cicada-ioc README §0](https://github.com/RiskAverseTech/cicada-ioc)
- The 10 red headings as restart points: not significant after correction — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
- jbo's notes point to GP sums, Möbius and Euler's totient (from Some Wisdom's "MOBIUS" word), and to sentence GP sums on the Parable — [yo-yo-yo-jbo/cicada_tools](https://github.com/yo-yo-yo-jbo/cicada_tools)
- LiberPrayground ships a Möbius sequence file (`seq_moebius`) alongside primes, primes to 3301, non-primes, Fibonacci and Lucas numbers for keystream tests — [LiberPrayground solver.py](https://github.com/relikd/LiberPrayground/blob/master/solver.py)
- Cicada's book-code conventions:
  - 2012 Mabinogion and Agrippa: line:character, counting spaces, on Cicada's own line wrap.
  - 2012 Blake: plate 4, 22/22.
  - 2014 Self-Reliance: paragraph:sentence:word:letter.
  - 2014 GEB: dialogue:line:word:letter.
  - Applying these formats to LP2's own numbers gave "no message".
  - Sources: [pnotisdev FINDINGS.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/FINDINGS.md); [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md); [scream314 2014.md](https://github.com/scream314/cicada3301/blob/master/2014.md)

### Inferences
- The concrete hint vocabulary is a short list: primes, totient, Möbius, Gematria sums of words and lines, 3301 and 1033, magic squares, book codes, and the "words, meaning, numbers" triad. The solved-page keys already used primes plus totient (An End) and solved-text words (DIVINITY, CIRCUMFERENCE).
- A lab should treat "their numbers are the direction" as the most specific unexhausted hint. One reading: word Gematria sums choose the key-pointer step, the sign (Vigenère or Beaufort), or the direction. Only parts of this have been swept.
- The An End hash implies at least one more artifact exists off-book. If LP2's key is that page, no in-book attack can succeed. cicada-ioc gives this 40% and pnotisdev about 50%; both are judgments.

### Gaps
- I could not access the wiki's "Liber Primus Ideas and Suggestions" page directly, so its full list of hypotheses (e.g. counting spaces as runes, gematria-based shifts) is known only by citation and search snippet.
- There is no authoritative statement on the red-rune positions in LP2 or the "Mobius" hypothesis beyond what is cited above.

## Q4. Which community resources are authoritative, and what tooling do they provide?

### Takeaway
- **Transcription:** rtkd/iddqd is the community master transcription. Taiiwo/cicada and LiberPrimusSolver match it rune for rune.
- **History:** scream314/cicada3301 is the best reachable walkthrough of the history and assets.
- **Tooling:** relikd/LiberPrayground provides interactive and solver tooling, including interrupt search.
- **Wiki:** the Uncovering Cicada wiki is the canonical history and ideas wiki (129 articles), though it was unreachable here.
- **Discussion:** CicadaSolvers Discord and r/cicada.
- **2026 ledgers:** pnotisdev, RiskAverseTech/cicada-ioc, Dukotah, jens-wedin, wazar and Leo-Y-Zhang are the most detailed negative-result ledgers, with planted-key controls. A new lab should diff against them before sweeping.

### Cited Findings
- **rtkd/iddqd**
  - "Unmodified files, transcription and other assets": a master transcription with delimiters (word `-`, clause `.`, line `/`, paragraph `&`, segment `$`, chapter `§`, page `%`), plus a sentences file, index, keys, translation and known plaintext.
  - Last push 2023-08-15, pinned commit f2267b0.
  - Taiiwo/cicada is rune-for-rune identical to it. r4nd0mD3v3l0p3r/LiberPrimusSolver's unsolved.txt covers exactly LP2 0-57.
  - Source: [cicada-ioc SOURCES.md](https://github.com/RiskAverseTech/cicada-ioc/blob/main/SOURCES.md)
- **Transcription errata**
  - An independent OCR re-read found one rune-order error on a solved page (book page 9, BELEIUE → BELIEUE) and five byte errors in the 256-byte payload — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md); [cicada-ioc SOURCES.md](https://github.com/RiskAverseTech/cicada-ioc/blob/main/SOURCES.md)
- **relikd/LiberPrayground** — [LiberPrayground README](https://github.com/relikd/LiberPrayground)
  - `playground.py`: translate, rotate (29 variants), crib-to-key "d", find words by length, key manipulation (invert, shift, rotate, offset, pad), interrupt highlighting, and prime and emirp checks with word/line Gematria sums.
  - `solver.py -s`: reproduces all solved pages.
  - `probability.py`: IoC, and Vigenère and Affine key guessing by least-squares distance to English rune frequencies.
  - `GuessPattern`, `InterruptSearch` (all, sequential, genetic) and `InterruptDB` (precomputed, with an HTML results overview).
  - The OEIS checker and a rune n-gram builder.
  - The pages were "double checked … each and every rune".
- **scream314/cicada3301** — [scream314 README](https://github.com/scream314/cicada3301)
  - Year-by-year walkthroughs for 2012-2017, full LP images in assets/2014/liber-primus-complete (00-74.jpg, 2400×3600 per cicada-ioc), Gematria Primus, a pages-and-ciphers table, and "possible hints, never used".
  - Credits #cicadasolvers IRC on freenode ("defunct?") and the CicadaSolvers Discord.
  - Sources: [scream314 README](https://github.com/scream314/cicada3301); [cicada-ioc SOURCES.md](https://github.com/RiskAverseTech/cicada-ioc/blob/main/SOURCES.md)
- **Other tool repositories** — [search results](https://github.com/Taiiwo/cicada)
  - Taiiwo/cicada: a library for LP pages and lines.
  - yo-yo-yo-jbo/cicada_tools: Python experiments framework.
  - lipeeeee/gematria: hashing and Gematria sums.
  - r4nd0mD3v3l0p3r/LiberPrimusSolver (Node).
  - krisyotam/cicada3301: an archive bundling solver repos such as jbo-tools, idkfa and aadishgoel.
  - The "cicada-solvers" GitHub organization is described as forks of associated projects. I could not confirm its current contents.
- **Uncovering Cicada wiki**
  - 129 articles, fetched via the MediaWiki API on 2026-10-21 by pnotisdev, CC-BY-SA — [pnotisdev SOURCES.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/SOURCES.md)
  - Key pages: "How the solved pages of the Liber Primus were solved", "Liber Primus Ideas and Suggestions", "Frequency Analysis Unsolved Pages", "What Happened (2012)" — [cicada-ioc README §11](https://github.com/RiskAverseTech/cicada-ioc); [wiki URL](https://uncovering-cicada.fandom.com/wiki/How_the_solved_pages_of_the_Liber_Primus_were_solved)
- **Collaborative community**
  - The DEF CON 31 (2023) talk "Cracking Cicada 3301: The Future of Collaborative Puzzle-Solving" covers CicadaSolvers' ongoing LP effort (search snippet only) — [DEF CON forum](https://forum.defcon.org/node/246097)
  - The CicadaSolvers Discord is a private server. pnotisdev audited its threads in 2026-10 but did not redistribute them — [pnotisdev SOURCES.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/SOURCES.md)
- **2026 negative-result ledgers**
  - pnotisdev: a 148-row registry.toml, TRIED.md and FINDINGS.md — [pnotisdev TRIED.md](https://github.com/pnotisdev/cicada3301/blob/15200c67abee106913ba01ff504c5b6e88d16cc7/docs/TRIED.md)
  - RiskAverseTech/cicada-ioc: 84 sections and "1.24 B decoder tests", frozen v1.0 on 2026-11-01. Its `results/ledger_diff.md` diffs families against the other labs — [cicada-ioc](https://github.com/RiskAverseTech/cicada-ioc)
  - Dukotah/cicada3301: a 309-row LEDGER.json, a claimed-solve oracle, and plant-and-recover benchmarks; status as of 2026-11-05 — [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301)
  - Also: TheronEagle/liber-primus-research and murphyaidanbusiness-ux/liberprimus ("Claude's attempts"). These are AI-driven and unverified — [search results](https://github.com/TheronEagle/liber-primus-research)

### Inferences
- **Transcription:** pin rtkd/iddqd at commit f2267b0 and apply the BELIEUE erratum. The lab's own data/pages come from LiberPrayground and should be diffed against it.
- **Statistics as regression checks:** adopt the community's statistical constraints as regression tests for any new decoder. That means 86 doublets (23 across gaps), the lag-6 relation, the 2-rune-word deficit, the A/I oracle on 83 one-rune words, and prime clause sums.
- **Before any new sweep, diff against the existing ledgers.** cicada-ioc says the same: "diff the candidate family against the three ledgers". The pnotisdev registry and the Dukotah ledger are the most exhaustive.

### Gaps
- The LiberPrayground results HTML (InterruptDB output) and analysis page (relikd.github.io) were unreachable, so I could not include its per-page IoC numbers.
- The Dukotah LEDGER.json raw file path returned 404, so I have only its README summary.
- I could not verify the contents of the cicada-solvers GitHub organization or any published Discord summaries.
- The jens-wedin, wazar and Leo-Y-Zhang repositories are known only through cicada-ioc's citations; I did not fetch them.

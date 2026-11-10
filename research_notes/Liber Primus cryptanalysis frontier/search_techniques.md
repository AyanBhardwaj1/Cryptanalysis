# Search & Scoring Techniques for Automated Classical Cryptanalysis (applied to a 29-rune alphabet with known word boundaries)

Research date: 2026-11-10. Method note: WebSearch worked, but WebFetch was blocked at the network level for arxiv.org, www.cryptool.org and www.cs.mcgill.ca (getaddrinfo ENOTFOUND, outside the session's allowed domains). Full texts of the Lasry thesis, the Griffing paper, the Z340 paper and CipherBank therefore could not be read directly. Every number below comes from search-result excerpts of those primary sources and is attributed that way. Items marked "(background, unverified this session)" come from the researcher's prior knowledge and must not be cited as sourced facts.

---

## Q1. Scoring functions: n-grams vs word/dictionary vs neural LMs, IDP, normalisation, exploiting word boundaries

### Takeaway
Log-likelihood n-gram scoring is still the workhorse for every serious solver. Use quadgrams by default; AZdecrypt pushes to 8-grams with heavy optimisation. Neural LMs beat n-grams mainly on short or ambiguous ciphertexts, at large compute cost. Known word boundaries are the biggest structural advantage on offer: they enable pattern-word dictionary pruning and word-level scoring, both of which character n-grams ignore.

### Cited Findings
- **Standard log-likelihood n-gram fitness:** score = sum of log10 P(quadgram). Unseen n-grams get a floor probability F_floor = 0.01/(M − n + 1) to avoid log(0). Scores are always negative, and less negative means more English-like. — [Naskręcki, Ch. 9 Automated Cryptanalysis](https://bnaskrecki.faculty.wmi.amu.edu.pl/crypto/book/part3_polygraphic_ciphers/ch09_automated_cryptanalysis.html)
- The Practical Cryptography quadgram tables are built from the Leipzig Corpora Collection. One solver author normalised the summed score because a raw lower/higher sum "does not guarantee that the text is closer to English", which is why normalising (e.g. per n-gram, by length) is needed to compare candidates of different lengths. — [PlanetCalc Text fitness](https://planetcalc.com/8045)
- The Colossus solver (stblake) uses quadgram/quintgram log-likelihood as the primary fitness term, including for Vigenère. — [Colossus README](https://download.plaud.ai/stblake/colossus)
- **Higher-order n-grams:** "Most letter n-gram based solvers are limited to 5- or 6-grams, but because of its optimizations, AZdecrypt can support up to 8-grams." — [Oranchak, Blake, Van Eycke 2024, arXiv:2403.17350](https://arxiv.org/pdf/2403.17350)
- AZdecrypt changelog: a speed optimisation aborts n-gram scoring early once the new score cannot beat the old one. It "works especially well with sparse 7-grams or higher". — [AZdecrypt forum/changelog](https://forum.zodiackillerciphers.com/community/zodiac-cipher-mailings-discussion/azdecrypt-1-19b/paged/6/); [AZdecrypt GitHub](https://github.com/doranchak/azdecrypt)
- **Lasry's IDP (Index of Digraphic Potential, 2013):** used on the Schmeh double-transposition challenge. It is described as "highly selective for the right K2 and also monotonic for partially correct K2 keys", so it suits hill climbing on one key while the other is still unknown. This is the "specialised scoring for a sub-problem" principle. — [Lasry et al., Double Transposition divide-and-conquer (ResearchGate)](https://www.researchgate.net/publication/263286752_Solving_the_Double_Transposition_Challenge_with_a_Divide-and-Conquer_Approach)
- **Two-phase / two-dimensional fitness:** Lasry's long-key columnar transposition attack uses a two-phase hill climb with a two-dimensional fitness score and recovers keys up to 1,000 elements long. — [Lasry, Kopal, Wacker, Cryptologia 2016 (ResearchGate)](https://www.researchgate.net/publication/292669084_Cryptanalysis_of_columnar_transposition_cipher_with_long_keys)
- A 2026 ADFGVX paper uses IoC scoring with hill climbing to recover the transposition key, then n-gram modelling for the substitution stage. This is a cheap statistic for the outer layer and a language model for the inner one. — [Breaking the ADFGVX Cipher (ResearchGate, 2026)](https://www.researchgate.net/publication/399040382_Breaking_the_ADFGVX_Cipher_From_Theory_to_Practical_Cryptanalysis)
- **Neural LM scoring:** Kambhatla, Mansouri & Sarkar (EMNLP 2018) use beam search that scores the entire candidate plaintext with a neural LM, plus a neural "rest cost" estimate. On Zodiac-408 they report 1.2% symbol error rate (SER) with a 1M beam, against 2% SER for a 6-gram LM beam search with a 10M beam. The SER figures come from a third-party review. — [ACL Anthology D18-1102](https://aclanthology.org/D18-1102/); [Liner review](https://liner.com/review/decipherment-substitution-ciphers-with-neural-language-models)
- Neural LMs "have much lower perplexities than widely-used n-gram models" and "can distinguish between candidate plaintexts that resemble English at a distance" (applied to historical dictionary codes, 2020). — [arXiv:2010.04746](https://ar5iv.labs.arxiv.org/html/2010.04746)
- Bruton, Beloucif & Megyesi (arXiv:2606.05078, June 2026, preprint) train attention-augmented LSTMs end to end on aligned ciphertext–plaintext pairs, with no external LM and no key search. They report "near-perfect character-level decryption accuracy" on homophonic ciphers, including short and noisy ones. This is a supervised seq2seq approach, not a scoring function for key search. — [arXiv:2606.05078](https://arxiv.org/html/2606.05078)
- **Word boundaries and pattern words:** A word's repeat-letter "pattern" (e.g. ABA) restricts which plaintext words it can be. A dictionary indexed by pattern allows fast lookup, and practical workflows start from the longest pattern word. Without spaces the solver loses the word-pattern attack and falls back on letter/bigram statistics. — [Daily Cipher Aristocrat guide](https://www.thedailycipher.org/learn/aristocrat.html); [cipherdecipher guide](https://www.cipherdecipher.com/blog/aristocrat-cipher-guide); [The Black Chamber](https://theblackchamber552383191.wordpress.com/2020/11/19/aristocrats-and-patristocrats-refinements-on-solving/)
- Automated dictionary solvers: Hart (1994) maximised the number of decoded words found in a dictionary via tree search. Olson (2007) made it faster and handled short ciphertexts and non-dictionary words. — [ALICE, arXiv:2509.07282 (related-work section)](https://arxiv.org/pdf/2509.07282)
- **Running-key and word LMs:** Reddy & Knight (ACL 2012) use Gibbs sampling with a *word-level* LM. They report beating Viterbi with character models because word models are hard to use inside Viterbi. — [ACL Anthology P12-2016](https://aclanthology.org/P12-2016/)

### Inferences
- **Alphabet adaptation (arithmetic):** For 29 symbols, a dense quadgram table has 29^4 = 707,281 entries (≈2.8 MB as float32, ≈1.4 MB as int16). It fits in L2/L3 cache, so dense array indexing (idx = ((a·29+b)·29+c)·29+d) is the right design. Pentagrams are 29^5 ≈ 20.5M entries (≈82 MB float32, 41 MB int16), which is still feasible but cache-hostile. 6-grams and above need hashing or sparse tables, which is presumably why AZdecrypt adds early-abort and "sparse" n-gram tricks.
- **Corpus problem specific to runes:** Gematria-Primus runes map to English letters and digraphs (TH, EO, NG, OE, AE, IA/IO, EA, etc.). N-gram tables must be built by transliterating a large English corpus into the 29-rune alphabet with the same greedy digraph rules used on the solved pages. Otherwise the statistics will not match. A small rune-domain corpus (the solved LP pages) is too small for 4-grams or more, so use a large English corpus mapped to runes. This is the researcher's inference, not from a source.
- **Word boundaries:** With known word lengths, a cheap and highly selective scoring term is the fraction of decrypted words (or characters inside such words) that appear in a rune-transliterated dictionary, weighted by length. Combine it with n-grams computed *within words plus a word-boundary token*, i.e. treat the separator as a 30th symbol in the n-gram model. Including the boundary token captures word-initial and word-final statistics (e.g. "-ING", "THE"), which are strong signals. Pattern-word pre-filtering can also prune keys or cribs: for a periodic cipher, a crib hypothesis "word w at position i" fixes key letters directly.
- **Normalise for comparability:** When comparing candidates of different lengths or with different nulls removed, use mean log-prob per n-gram. Also consider a z-score against the distribution of scores for random rune text of the same length. Without this, null-deletion hypotheses get spurious credit.
- **Two-stage scoring (Lasry principle):** Use a cheap, monotonic statistic (IoC or a periodic-IoC sum) for outer parameters such as period, offsets and interrupter positions. Use the full n-gram plus dictionary score only for the inner key.

### Gaps
- No direct head-to-head numbers for quadgram vs 5/6/8-gram vs word-LM success rates as a function of ciphertext length. The relevant tables are in the Lasry thesis and the Kopal 2019 paper, which could not be fetched.
- The Reddy & Knight per-length accuracy table could not be verified (see Q3 for a conflicting attribution).
- No source found that quantifies how much known word boundaries lower the needed ciphertext length for Vigenère-type ciphers.

---

## Q2. Search algorithms: HC vs SA vs restarts vs GA/beam; Lasry, CrypTool 2, AZdecrypt, Z340

### Takeaway
The consensus of the strongest practitioners (Lasry/Kopal/Wacker, CrypTool 2, AZdecrypt) is: (1) hill climbing or simulated annealing with many random restarts; (2) specialised, selective scoring per stage; (3) divide-and-conquer to shrink the keyspace. Genetic algorithms are not what record-setting results use. Beam search with strong LMs is the NLP community's alternative for substitution/homophonic ciphers.

### Cited Findings
- **Lasry thesis:** "A Methodology for the Cryptanalysis of Classical Ciphers with Search Metaheuristics", University of Kassel, 2018, ISBN 978-3-7376-0458-1, open access (≈227–247 pp). It centres on local-search metaheuristics, mainly hill climbing and simulated annealing. — [dblp](https://dblp.org/rec/phd/dnb/Lasry18.html); [Kassel University Press OA PDF](https://www.uni-kassel.de/upress/online/OpenAccess/978-3-7376-0458-1.OpenAccess.pdf); [Google Books](https://books.google.com/books/about/A_Methodology_for_the_Cryptanalysis_of_C.html?id=YI9NDwAAQBAJ)
- **Hagelin M-209 (Lasry, Kopal, Wacker, Cryptologia 2018):** nested hill climbing and simulated annealing, ciphertext-only. Works on ciphertexts as short as 500 letters, against the 750–1,250 letters earlier methods needed. An earlier paper by the same authors needed 750 letters against 2,000–2,500 for prior work. — [Semantic Scholar](https://www.semanticscholar.org/paper/Ciphertext-only-cryptanalysis-of-Hagelin-M-209-pins-Lasry-Kopal/c4356f47fa9a2749b059d0fbf40d4cfea10df802); [ResearchGate](https://www.researchgate.net/publication/283162877_Ciphertext-only_cryptanalysis_of_Hagelin_M-209_pins_and_lugs)
- **Playfair:** Lasry, Kopal & Wacker's SA ciphertext-only attack recovers key and plaintext from as few as 75 letters. A 40-letter Playfair challenge was solved with CrypTool 2. — [Solving a 40-Letter Playfair Challenge with CrypTool 2 (HistoCrypt 2019)](https://ep.liu.se/ecp/158/010/ecp19158010.pdf)
- **Columnar transposition:** a two-phase hill climbing attack recovers keys up to 1,000 elements and is described as the best known algorithm for complete and incomplete columnar transposition. — [Cryptologia 2016 (ResearchGate)](https://www.researchgate.net/publication/292669084_Cryptanalysis_of_columnar_transposition_cipher_with_long_keys)
- **Double transposition:** solved with divide-and-conquer, hill climbing first on K2 with IDP, then on K1. — [ResearchGate](https://www.researchgate.net/publication/263286752_Solving_the_Double_Transposition_Challenge_with_a_Divide-and-Conquer_Approach)
- **Homophonic substitution in CrypTool 2:** Kopal (HistoCrypt 2019) uses simulated annealing with a *fixed temperature*, in semi-automatic and fully automatic modes. — [ecp19158012.pdf](https://ep.liu.se/ecp/158/012/ecp19158012.pdf); [ResearchGate](https://www.researchgate.net/publication/337425143_Cryptanalysis_of_Homophonic_Substitution_Ciphers_Using_Simulated_Annealing_with_Fixed_Temperature)
- A 2021 eprint notes that a ≈9,000-char homophonic ciphertext with a 65-symbol alphabet took ≈3 minutes to decrypt. The snippet does not say which method. — [Chhatrapati, eprint 2021/1005](https://eprint.iacr.org/2021/1005.pdf)
- **AZdecrypt** (Jarl Van Eycke, 2014, FreeBASIC) uses "a highly tuned, optimized, and specialized simulated annealing algorithm" over letter n-grams. It ranks every plaintext result. — [arXiv:2403.17350](https://arxiv.org/pdf/2403.17350); [GitHub doranchak/azdecrypt](https://github.com/doranchak/azdecrypt)
- AZdecrypt changelog: one solver change made 500,000 iterations do the work of ≈1,000,000 earlier ones, at a ≈20% per-iteration slowdown. Iteration count is a key tunable parameter. — [AZdecrypt forum](https://forum.zodiackillerciphers.com/community/zodiac-cipher-mailings-discussion/azdecrypt-1-19b/paged/6/)
- **Z340 solve (Dec 2020):** On 2 Dec 2020, Blake and Oranchak ran a batch of **655,088 transposition variations** of Z340 through AZdecrypt, i.e. an outer enumeration of structural hypotheses with the fast inner homophonic solver per hypothesis and ranking by score. Solution validated by FBI ~Dec 2020 (secondary sources disagree on the exact date). — [arXiv:2403.17350](https://arxiv.org/abs/2403.17350); [The Register](https://www.theregister.com/2020/12/12/zodiac_killers_cipher_solved/)
- **Beam search in NLP:** "Beam Search for Solving Substitution Ciphers" (Nuhn, Schamper, Ney, ACL 2013) and the neural-LM beam search of Kambhatla et al. 2018 use beams of up to 10M (6-gram) or 1M (neural) for Zodiac-408. — [ACL P13-1154](https://aclanthology.org/P13-1154.pdf); [Liner review of D18-1102](https://liner.com/review/decipherment-substitution-ciphers-with-neural-language-models)
- **General:** SA escapes local optima at the cost of slower exploration. At zero temperature it degenerates into hill climbing. — [Adaptive simulated annealing, arXiv cs/0001018](https://arxiv.org/pdf/cs/0001018)

### Inferences
- **Recipe for this lab:**
  - Outer loop: enumerate structural hypotheses (period, cipher variant Vig/Beaufort/variant-Beaufort, interrupter rule, key offset, direction). Z340-style, run thousands to hundreds of thousands of variants.
  - Inner loop: (a) for periodic Vigenère/Beaufort with known period, *don't* use metaheuristics for the shift keys. Use exact per-column optimisation (each column is independent under unigram/IoC scoring) and then coordinate-wise refinement under quadgram scoring. Each pass is p × 29 evaluations. (b) For autokey and mixed-alphabet variants, use SA/HC with shotgun restarts. (c) For substitution layers, use SA with fixed or slowly decreasing temperature (Kopal/AZdecrypt style).
- **Lasry thesis principles** (background, unverified this session; the PDF could not be fetched):
  - Use hill climbing or SA rather than GAs.
  - Use many restarts with good (non-random) initial keys.
  - Choose scoring functions for *selectivity* (sharp peak at the right key) and *resilience* (still rewards partially correct keys).
  - Use high-coverage neighbourhoods (all swaps, segment moves) with a smooth landscape.
  - Reduce the search space via divide-and-conquer.
  - Use adaptive scoring: switch from IoC/IDP to n-grams as the key improves.

  The cited results above (IDP being monotonic for partially correct keys, two-phase fitness, nested HC/SA for M-209) are consistent with this summary.
- GAs: no source in this search reports GAs beating SA/HC on any classical cipher class. Treat as low priority.

### Gaps
- Exact SA temperatures, cooling schedules and restart counts from the Lasry thesis and the CrypTool 2 Vigenère/autokey analyzers were not retrievable (fetch blocked).
- No published success-rate tables were obtained for CrypTool 2's Vigenère Analyzer or for autokey solvers.

---

## Q3. Running-key / two-text problems (plaintext and key both natural language)

### Takeaway
Use a character n-gram Markov model over joint (plaintext, key) pairs and decode with Viterbi or beam search (Griffing 2006, 6-grams, "most of the plaintext most of the time"). Alternatively, use Gibbs sampling with word-level LMs (Reddy & Knight 2012), which is better and faster. Recovery is high at around 1,000 characters and poor at very short lengths. Plaintext/key swaps are inherent, and accuracy is measured as max(plaintext match, key match).

### Cited Findings
- Griffing, "Solving the Running Key Cipher with the Viterbi Algorithm", Cryptologia 30(4):361–367, 2006. Viterbi "is able to reconstruct most of the plaintext from running key ciphertext most of the time using 6-gram letter statistics". A companion paper applies the same method to XOR-ed plaintext pairs (two-time pad). — [Wikipedia: Running key cipher](https://en.wikipedia.org/wiki/Running_key_cipher); [ResearchGate](https://www.researchgate.net/publication/220615828_Solving_the_Running_Key_Cipher_with_the_Viterbi_Algorithm); [Griffing XOR paper (SciSpace)](https://scispace.com/papers/solving-xor-plaintext-strings-with-the-viterbi-algorithm-8vgbl48q4h); [Cryptologia vol 30 TOC](https://sigmod.org/publications/dblp/db/journals/cryptologia/cryptologia30.html)
- Reddy & Knight, "Decoding Running Key Ciphers", ACL 2012 (short paper, pp. 80–84). Gibbs sampling with a word-level LM outperforms Viterbi with character models. The Gibbs sampler is described as orders of magnitude faster than Viterbi. Because plaintext and key are interchangeable, accuracy is scored as the better of plaintext match and key match. — [ACL Anthology](https://aclanthology.org/P12-2016/); [PDF](https://aclanthology.org/P12-2016.pdf); [ACM DL](https://dl.acm.org/doi/10.5555/2390665.2390686)
- **Reported accuracy (conflict):** A Wikipedia-derived snippet gives ≈88–93% of characters recovered on 1,000-character ciphertexts and ≈17–26% on 10-character ciphertexts for the Gibbs/word-LM method. The same snippet attributes the result to Griffing, while other sources credit Reddy & Knight. Treat the numbers as approximate and the attribution as probably Reddy & Knight. — [Wikipedia: Running key cipher](https://en.wikipedia.org/wiki/Running_key_cipher); attribution per [ACL Anthology](https://aclanthology.org/P12-2016/)

### Inferences
- **State-space size for 29 runes:** A Griffing-style Viterbi with n-gram order k over the plaintext has 29^(k−1) states; the key letter is determined by the ciphertext and the plaintext letter. If both plaintext and key histories are tracked, the state is (plaintext history, key history), giving 29^(2(k−1)) states. That is infeasible beyond k≈3 (29^4 ≈ 7×10^5 states per position, ×29 transitions), so beam-prune. Practical choice: beam search with a joint score of log P_LM(plaintext) + log P_LM(key), beam width 10^4–10^6, quadgram/5-gram LMs, plus a word-boundary-aware bonus on the plaintext side only. Known plaintext word boundaries constrain the plaintext stream strongly; the key stream's boundaries are unknown.
- **Shannon-style feasibility (back-of-envelope):** English carries ≈1–1.5 bits/char (background, unverified). Two English streams need ≈2–3 bits/char of total entropy, below log2(29) ≈ 4.86 bits/char. So the running-key problem is information-theoretically determined, consistent with the reported success. Short pieces (<≈100 chars) are expected to be highly ambiguous, consistent with the 17–26% recovery at 10 chars.
- **When the key text is a known book** (e.g. a candidate source text): sweep all offsets in the candidate text and score the plaintext. This costs O(N_book × L) and is trivially parallel and far more powerful than blind two-text decoding. Prioritise candidate key texts (including the solved LP pages themselves, and texts Cicada referenced) over blind Viterbi.

### Gaps
- Could not read Griffing's PDF (cs.mcgill.ca blocked) for exact per-length percentages, or the Reddy & Knight tables (only metadata and snippets). No source found for minimum running-key lengths with modern neural LMs (2020–2026).

---

## Q4. Interrupters / nulls / variable key alignment

### Takeaway
No published general-purpose algorithm turned up. Standard practice, and Z340's practice, is to enumerate structural hypotheses in an outer loop and score each with the fast inner solver. Liber Primus community tooling explicitly notes that interrupts break simple periodic analysis.

### Cited Findings
- LiberPrayground's periodic-cipher analysis splits text by key length but "does not take into account possible interrupts (commonly used in the Liber Primus)". It also notes that alternating two Vigenère keys produces long-period patterns that are hard to detect with IoC. — [LiberPrayground Cipher Analysis](https://relikd.github.io/LiberPrayground/results/analysis.html); [LP Analysis results](https://relikd.github.io/LiberPrayground/results)
- The solved-pages count is disputed: a workbench page says ≈19 solved / ≈56 unsolved, while a GitHub repo says 32 solved pages. — [Arethusa LP workbench](https://uranometria.pages.dev/liber-primus-workbench.html); [lipeeeee/gematria](https://github.com/lipeeeee/gematria)
- Z340 needed an outer enumeration of 655,088 transposition variants, each solved by AZdecrypt and ranked. This is an analogous "unknown structural layer" problem. — [arXiv:2403.17350](https://arxiv.org/pdf/2403.17350)

### Inferences
- **Interrupter model** (background, unverified: LP community lore holds that a specific rune, ᚠ/F, sometimes appears in plaintext without consuming a key letter). Model each occurrence of the candidate interrupter rune as a binary variable "consumes key / does not". For k occurrences there are 2^k alignments. Handle this with:
  - a DP/Viterbi over key-position state, where the state is the key index mod period and each interrupter-candidate position may advance or not, scored by n-grams (the n-gram history makes this a beam search);
  - or SA over the bit-vector, with a move that flips one bit and re-scores only the affected suffix. With word boundaries, prefer hypotheses where decrypted words land in the dictionary.
- **Unknown nulls** (inserted symbols to delete): same approach with a deletion bit-vector, plus a length-normalised score (see Q1) and a per-null prior penalty so the search cannot "delete its way" to good text.
- **Variable key alignment / reset at word or sentence or page boundaries:** enumerate reset rules (none / per word / per sentence / per page / per line) as the outer loop. Known word boundaries make per-word resets cheap to test.

### Gaps
- No academic paper found that benchmarks null/interrupter detection in periodic polyalphabetic ciphers. The CrypTool 2 docs (blocked) might contain relevant options.

---

## Q5. Performance engineering

### Takeaway
Reported throughput for state-of-the-art tools comes from tight compiled loops, multithreading, incremental scoring and early abort. AZdecrypt's headline: up to ~200 homophonic ciphers solved per second on an 8-core CPU at 99%+ solve rate.

### Cited Findings
- "On a modern 8-core CPU AZdecrypt can solve up to 200 homophonic substitution ciphers per second with a 99%+ solve rate." — [arXiv:2403.17350](https://arxiv.org/pdf/2403.17350)
- AZdecrypt uses about three-quarters of available CPU threads for solvers by default and has a "solver performance mode". It aborts n-gram scoring early when the candidate cannot beat the current score. — [AZdecrypt forum/changelog](https://forum.zodiackillerciphers.com/community/zodiac-cipher-mailings-discussion/azdecrypt-1-19b/paged/6/); [freebasic.net AZdecrypt thread](https://www.freebasic.net/forum/viewtopic.php?t=23188)
- No official iterations-per-second benchmark exists; forum users self-report iteration counts and MIPS. — [AZdecrypt forum](https://forum.zodiackillerciphers.com/community/zodiac-cipher-mailings-discussion/azdecrypt-1-19b/paged/6/)

### Inferences (engineering recommendations for Python/numba/C)
- **Incremental scoring:** For a substitution swap or a single key-letter change in a periodic cipher of period p, only n-grams overlapping changed positions need re-scoring. For a Vigenère key-letter change that is ≈L/p positions × n n-grams each, not L. Keep a per-position n-gram score array and update deltas.
- **Early-abort acceptance (AZdecrypt trick):** For hill climbing, accumulate the delta and stop as soon as it cannot reach the threshold. This needs an upper bound on per-n-gram log-prob, i.e. the table maximum. For SA, draw the random acceptance threshold *before* scoring, then abort early against it.
- **Tables:** dense int16 or float32 quadgram arrays indexed by base-29 rolling index (707k entries) in numba `@njit(cache=True, fastmath=True)`. Precompute the ciphertext as a uint8 array and pre-strip word separators, keeping a separate boundary mask.
- **Parallelism:** use `numba.prange` across restarts or structural hypotheses (embarrassingly parallel), or `multiprocessing` with one process per core and per-process RNG seeds. Avoid Python-level loops inside the inner loop. GPU only pays off for massive outer enumerations (e.g. book-offset sweeps for running key, or exhaustive short periods), where each thread scores one hypothesis.
- **Exhaustive where possible:** Vigenère/Beaufort with known period: per-column 29 options, so coordinate ascent is exact-ish and costs microseconds. Running-key over a known book: O(N_book × L) vectorised; numpy broadcasting or a numba loop gives ~10^8–10^9 char-ops/s on a modern core (an order-of-magnitude estimate, not sourced).

### Gaps
- No published Python/numba/GPU throughput numbers for classical-cipher scoring were found. CrypTool 2 and Lasry performance figures were not retrievable.

---

## Q6. LLMs in classical cryptanalysis (2023–2026)

### Takeaway
LLMs are poor at *doing* classical decryption arithmetic. On CipherBank (2025) the best models score below 50% overall, and Vigenère is near zero for most. LLMs also hallucinate confident wrong keys. The 2026 trend (DescryptTool) is to use LLMs as orchestrators that pick and drive fixed solvers, without free code execution. LLMs are also used to judge whether output is plausible language and to generate hypotheses, while deterministic solvers do the search.

### Cited Findings
- **CipherBank** (arXiv:2504.19093, Apr 2025; ACL Findings 2025): 2,358 decryption tasks across 9 algorithms. Best averages: Claude-3.5 45.14 and o1 40.59. On Vigenère, o1 scored **7.25** and DeepSeek-R1 **0.38**; DeepSeek-R1's overall average was 25.91. Models are "high name decryption errors"-prone. The authors conclude that reasoning optimisations "still inadequately address" cryptographic challenges. — [arXiv:2504.19093](https://arxiv.org/pdf/2504.19093); [CipherBank project page](https://cipherbankeva.github.io/); [ACL Findings PDF](https://aclanthology.org/2025.findings-acl.309.pdf); [HF dataset](https://huggingface.co/datasets/yu0226/CipherBank)
- An example shows DeepSeek-R1 decoding a Vigenère message and producing "a hallucinated answer and key which is totally wrong". — [TechRxiv zero-shot CoT cryptanalysis](https://www.techrxiv.org/doi/10.36227/techrxiv.175295517.70390739)
- The same TechRxiv preprint reports o1 at 75% and R1 at 55% on Vigenère, but its numbers are internally inconsistent (o1 is also given as 45%). Not reliable; it contradicts CipherBank. — [TechRxiv](https://www.techrxiv.org/doi/10.36227/techrxiv.175295517.70390739); contradicted by [CipherBank](https://cipherbankeva.github.io/)
- **Benchmarking LLMs for Cryptanalysis and Mismatched-Generalization** (arXiv:2505.24621, May 2025, revised 2026): GPT-4o Caesar exact-match rises from 0.66 to 0.90 with one in-context example. The paper also discusses partial decryption as a jailbreak vector. — [arXiv:2505.24621](https://arxiv.org/html/2505.24621v1)
- **Transformers via in-context learning** (arXiv:2508.10235): on monoalphabetic substitution, 100% decryption accuracy once 32 examples have been observed. That is a known-plaintext/ICL setting, not ciphertext-only. — [arXiv:2508.10235](https://arxiv.org/html/2508.10235)
- **ACTS** (arXiv:2609.26893, 2026): LLM cipher-identification "competence collapses when metadata is removed". Reasoning traces do not rescue blind performance, and classical supervised methods outperform LLM-centred pipelines, including agentic ones with Kali tools. — [arXiv:2609.26893](https://arxiv.org/pdf/2609.26893)
- **DescryptTool** (Kopal & Megyesi, Cryptologia, online 7 Sep 2026, open access, DOI 10.1080/01611194.2026.2693460): an agentic LLM workbench (DESCRYPT project). By design the LLM is "not allowed to generate arbitrary Python scripts, execute a code interpreter, or access the local shell". It drives fixed solvers instead. In their tests the agent identified the cipher family from statistics, "did not misclassify the cipher family and therefore always chose the correct solver". — [Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/01611194.2026.2693460)
- **CryptanalysisBench** (arXiv:2607.18538, Jul 2026): 191 tasks attacking real (modern) cryptographic schemes, with agents writing attack scripts. It is not about classical ciphers, but it is the code-execution evaluation setting. — [arXiv:2607.18538](https://arxiv.org/abs/2607.18538)
- **AICrypto** (arXiv:2507.09580, 2025) evaluates LLM cryptography capabilities more broadly. — [arXiv:2507.09580](https://arxiv.org/pdf/2507.09580)
- An open-source "AI-enabled application for cracking ciphers" exists (matthewdgreen/decipher); details not examined. — [GitHub](https://github.com/matthewdgreen/decipher)
- **False-progress caution:** a neural-network K4 attempt "placed the plaintext clues in the right place after 10k epochs", which "gives the false hope of solving it". Models can regurgitate cribs. — [kryptos-k4-neural-network-attempt](https://github.com/mmtmn/kryptos-k4-neural-network-attempt)

### Inferences
- **For this lab:** never let an LLM do the modular arithmetic or claim a decryption. Good uses:
  - (a) Hypothesis generation: which cipher variants, key sources or interrupter rules to enqueue for the deterministic outer loop.
  - (b) Judging the top-k solver outputs for semantic plausibility, where neural/LLM perplexity is a better discriminator than n-grams for "English at a distance" (consistent with arXiv:2010.04746).
  - (c) Crib and key-text suggestion, e.g. candidate source texts for a running key.
  - (d) Summarising and logging.

  Verify every LLM claim by re-running the deterministic decrypt. This mirrors the DescryptTool design (LLM selects and parameterises fixed solvers) and the CipherBank/ACTS evidence that the models fail at the raw computation and at blind identification.
- An LLM perplexity re-ranker is affordable only at the end of the pipeline (top ~10–1000 candidates), not in the inner loop. The inner loop must use n-gram tables.

### Gaps
- No source found evaluating LLMs on rune or non-Latin classical ciphers, or on ciphers with word boundaries specifically.
- DescryptTool's quantitative solve rates were not retrievable. No peer-reviewed study of LLM-as-plausibility-judge accuracy against n-gram scoring was found.

# Data

- `pages/*.txt`: Liber Primus rune transcription by relikd, from
  https://github.com/relikd/LiberPrayground (`pages/`). `solved_*.txt` hold the published
  plaintext (in runes) of the solved sections. Separators: `•` space, `⁘` period, `⁚` comma,
  `⁖` semicolon, `⁜` chapter mark. The upstream repository has no license file; the LP itself
  is Cicada 3301's public puzzle text. Credit to relikd for the careful transcription.
- `ngrams.npz`: rune-space unigram/bigram/quadgram log10 tables.
- `vocab.txt.gz`: rune-spelled English vocabulary with counts.

Both generated files come from `scripts/build_ngrams.py` run over the NLTK Gutenberg sample
(public-domain texts: KJV Bible, Milton, Blake, Whitman, Melville, Austen, Shakespeare, ...)
plus the solved LP plaintext:

    curl -LO https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/gutenberg.zip
    unzip gutenberg.zip && python scripts/build_ngrams.py gutenberg/

"""Build data/ngrams.npz from a folder of plain-text English files plus the solved LP pages.

Usage: python scripts/build_ngrams.py CORPUS_DIR [--lp-weight 20]

The corpus used for the committed table is the NLTK Gutenberg sample (public domain):
https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/gutenberg.zip
LP plaintext is repeated ``--lp-weight`` times so its vocabulary (DIVINITY, PRIMES, ...)
carries weight against the much larger English corpus.
"""

from __future__ import annotations

import argparse
import gzip
import re
from collections import Counter
from pathlib import Path

from lplab import corpus, ngram
from lplab.gematria import indices_to_runes, latin_to_indices

VOCAB_PATH = ngram.NGRAM_PATH.with_name("vocab.txt.gz")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus_dir", type=Path)
    ap.add_argument("--lp-weight", type=int, default=20)
    args = ap.parse_args()

    streams = []
    words: Counter[str] = Counter()
    for f in sorted(args.corpus_dir.glob("*.txt")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        for w in re.findall(r"[A-Za-z]+", text):
            words[indices_to_runes(latin_to_indices(w))] += 1
        # one stream per paragraph keeps n-grams from bridging unrelated text
        for para in re.split(r"\n\s*\n", text):
            idx = latin_to_indices(para)
            if idx.size >= 4:
                streams.append(idx)
        print(f"{f.name}: {len(streams)} streams so far")
    lp = [corpus.load_solution(n).runes for n in corpus.SOLVED]
    for n in corpus.SOLVED:
        for w in re.split(r"[^\u16a0-\u16ff]+", corpus.load_solution(n).raw):
            if w:
                words[w] += args.lp_weight
    streams.extend(lp * args.lp_weight)
    model = ngram.train(streams)
    ngram.save(model)
    print(f"saved {ngram.NGRAM_PATH}")
    kept = [(w, c) for w, c in words.most_common() if c >= 3 or len(w) <= 2]
    with gzip.open(VOCAB_PATH, "wt", encoding="utf-8") as fh:
        fh.writelines(f"{w}\t{c}\n" for w, c in kept)
    print(f"saved {VOCAB_PATH} ({len(kept)} words)")


if __name__ == "__main__":
    main()

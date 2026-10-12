"""BM25 lexical retriever over the shared Japanese-aware tokenizer."""

from __future__ import annotations

from typing import List

from rank_bm25 import BM25Okapi

from app.retrieval.base import Hit, Retriever
from app.retrieval.tokenizer import tokenize


class BM25Retriever(Retriever):
    """Lexical BM25 (Okapi). Japanese runs -> character bigrams; Latin -> lowercase words.

    Dictionary-style corpora: chunks whose headword (section_title) matches query
    tokens get a headword boost, because for a glossary the entry IS the document
    identity (long definitions otherwise lose to short mentions via length norm).
    """

    method = "bm25"
    HEADWORD_BOOST = 3.0

    def __init__(self, chunks: List[dict]):
        super().__init__(chunks)
        self._tokenized_corpus = [tokenize(t) for t in self._texts()]
        empty = sum(1 for t in self._tokenized_corpus if not t)
        if empty == len(self._tokenized_corpus):
            raise ValueError("corpus tokenized to empty; cannot build BM25 index")
        self._bm25 = BM25Okapi(self._tokenized_corpus)
        # headword token sets: section_title AND the leading "term（reading）" part
        # of text (glossary chunks start with their headword).
        self._section_tokens = []
        for c in self.chunks:
            toks = set(tokenize(str(c.get("section_title") or "")))
            text = str(c.get("text", "") or "")
            head = text.split("（", 1)[0].split("(", 1)[0]
            if head and len(head) <= 30:
                toks |= set(tokenize(head))
            self._section_tokens.append(toks)

    def search(self, query: str, top_k: int = 5) -> List[Hit]:
        if top_k <= 0:
            return []
        q = tokenize(query)
        if not q:
            return []
        scores = self._bm25.get_scores(q)
        qset = set(q)
        for i, sec in enumerate(self._section_tokens):
            if sec and qset & sec:
                scores[i] *= self.HEADWORD_BOOST
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :top_k
        ]
        hits: List[Hit] = []
        for i in order:
            if scores[i] <= 0:
                break  # no lexical overlap at all
            hits.append(self.hit_from_index(i, scores[i]))
        return hits

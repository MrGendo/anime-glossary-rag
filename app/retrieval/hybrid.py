"""Hybrid retriever: min-max normalized BM25 + vector scores, alpha-weighted."""

from __future__ import annotations

from typing import List, Optional, Sequence

from app.retrieval.base import Hit, Retriever


def minmax_normalize(scores: Sequence[float]) -> List[float]:
    """Min-max normalize to [0, 1]; all-equal scores map to 0.0 (no signal)."""
    n = len(scores)
    if n == 0:
        return []
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-12:
        return [0.0] * n
    return [(s - lo) / (hi - lo) for s in scores]


class HybridRetriever(Retriever):
    """``score = alpha * norm(vector) + (1 - alpha) * norm(bm25)`` (alpha=0.5).

    Fetches ``fetch_k`` (default max(top_k*4, 20)) candidates from each leg,
    min-max normalizes per-leg score distributions over the *union* of
    candidates, then weights and merges. Works even if the vector leg is
    unavailable -- pass ``vector=None`` for BM25-only hybrid behavior.
    """

    method = "hybrid"

    def __init__(
        self,
        chunks: List[dict],
        *,
        bm25: Optional[Retriever] = None,
        vector: Optional[Retriever] = None,
        alpha: float = 0.5,
        fetch_k: int = 20,
    ):
        super().__init__(chunks)
        if bm25 is None:
            from app.retrieval.bm25 import BM25Retriever

            bm25 = BM25Retriever(chunks)
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")
        self.bm25 = bm25
        self.vector = vector
        self.alpha = float(alpha)
        self.fetch_k = int(fetch_k)

    @classmethod
    def from_components(
        cls,
        bm25: Retriever,
        vector: Optional[Retriever],
        *,
        alpha: float = 0.5,
        fetch_k: int = 20,
    ) -> "HybridRetriever":
        """Build from already-constructed retrievers (chunk lists must match)."""
        obj = cls.__new__(cls)
        Retriever.__init__(obj, bm25.chunks)
        obj.bm25 = bm25
        obj.vector = vector
        obj.alpha = float(alpha)
        obj.fetch_k = int(fetch_k)
        return obj

    def search(self, query: str, top_k: int = 5) -> List[Hit]:
        if top_k <= 0 or not query.strip():
            return []
        k = max(self.fetch_k, top_k)
        lex = self.bm25.search(query, top_k=k) if self.bm25 else []
        vec = self.vector.search(query, top_k=k) if self.vector else []

        bm25_scores: dict = {h.chunk_id: h.score for h in lex}
        vec_scores: dict = {h.chunk_id: h.score for h in vec}
        ids = list(dict.fromkeys([*bm25_scores, *vec_scores]))
        if not ids:
            return []

        nb = minmax_normalize([bm25_scores.get(i, 0.0) for i in ids])
        nv = minmax_normalize([vec_scores.get(i, 0.0) for i in ids])
        fused = {
            i: self.alpha * v + (1.0 - self.alpha) * b
            for i, b, v in zip(ids, nb, nv)
        }

        by_id: dict = {h.chunk_id: h for h in (*lex, *vec)}
        id_to_chunk_idx: dict = {
            str(c["chunk_id"]): idx for idx, c in enumerate(self.chunks)
        }
        ranked = sorted(ids, key=lambda i: fused[i], reverse=True)[:top_k]
        hits: List[Hit] = []
        for i in ranked:
            if fused[i] <= 0.0:
                continue
            src = by_id.get(i)
            if src is not None:
                hits.append(
                    src.model_copy(update={"score": float(fused[i]), "method": "hybrid"})
                )
            else:
                idx = id_to_chunk_idx[i]
                hits.append(self.hit_from_index(idx, fused[i]))
        return hits

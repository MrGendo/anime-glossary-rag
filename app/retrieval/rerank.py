"""Hybrid retrieval + optional cross-encoder rerank of the top-N candidates."""

from __future__ import annotations

from typing import List, Optional

from app.retrieval.base import Retriever
from app.retrieval.hybrid import HybridRetriever

DEFAULT_RERANK_MODEL = "cross-encoder/multilingual-MiniLM-L12-v2"


class HybridRerankRetriever(Retriever):
    """Hybrid retriever whose top ``rerank_k`` (default 20) candidates are
    re-scored by a cross-encoder; final ranking = rerank scores.

    The cross-encoder is an optional dependency at construction time: if it
    cannot be loaded (package missing / model download failed), the
    constructor raises ``NotImplementedError`` so an upper layer can degrade
    to plain ``HybridRetriever``.
    """

    method = "hybrid_rerank"

    def __init__(
        self,
        chunks: List[dict],
        *,
        hybrid: Optional[HybridRetriever] = None,
        rerank_model: str = DEFAULT_RERANK_MODEL,
        rerank_k: int = 20,
        alpha: float = 0.5,
    ):
        super().__init__(chunks)
        if hybrid is None:
            hybrid = HybridRetriever(chunks, alpha=alpha)
        self.hybrid = hybrid
        self.rerank_model = rerank_model
        self.rerank_k = int(rerank_k)

        self._cross: Optional[object] = None
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as e:
            raise NotImplementedError(
                "CrossEncoder unavailable (sentence-transformers not "
                f"installed): {e}; degrade to HybridRetriever"
            ) from e
        try:
            self._cross = CrossEncoder(rerank_model, device="cpu")
        except Exception as e:
            raise NotImplementedError(
                f"failed to load rerank model '{rerank_model}' "
                f"({e.__class__.__name__}: {e}); degrade to HybridRetriever"
            ) from e

    def search(self, query: str, top_k: int = 5) -> List[Hit]:
        if top_k <= 0 or not query.strip():
            return []
        cands = self.hybrid.search(query, top_k=max(self.rerank_k, top_k))
        if not cands:
            return []
        if self._cross is None:  # pragma: no cover - guarded by constructor
            return cands[:top_k]
        pairs = [(query, self.chunks_text(c.chunk_id, c.text_snippet)) for c in cands]
        scores = self._cross.predict(pairs)
        scored = sorted(zip(cands, scores), key=lambda p: p[1], reverse=True)[:top_k]
        return [
            h.model_copy(update={"score": float(s), "method": self.method})
            for h, s in scored
        ]

    # ------------------------------------------------------------------ util
    def chunks_text(self, chunk_id: str, fallback: str = "") -> str:
        for c in self.chunks:
            if str(c["chunk_id"]) == chunk_id:
                return str(c.get("text", "") or "") or fallback
        return fallback

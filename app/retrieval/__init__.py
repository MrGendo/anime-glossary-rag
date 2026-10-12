"""Retrieval layer for the anime-terminology vertical RAG project.

Unified interface:

    class Retriever:
        def search(self, query: str, top_k: int = 5) -> list[Hit]

Implementations:
    BM25Retriever          -- lexical BM25 (rank-bm25), Japanese char-bigram tokenizer
    VectorRetriever        -- sentence-transformers embeddings + FAISS (CPU)
    HybridRetriever        -- min-max score normalization + alpha-weighted fusion
    HybridRerankRetriever  -- hybrid retrieval + cross-encoder rerank of top-N

All retrievers are constructed from ``chunks: list[dict]`` following the
data/processed/chunks.jsonl schema (chunk_id, text, source_id, source_title,
source_type, page_number, timestamp, section_title, language,
extraction_method, verification_status, extra) and offer ``from_jsonl(path)``.
"""

from app.retrieval.base import Hit, Retriever
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector import VectorRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.rerank import HybridRerankRetriever
from app.retrieval.tokenizer import tokenize

__all__ = [
    "Hit",
    "Retriever",
    "BM25Retriever",
    "VectorRetriever",
    "HybridRetriever",
    "HybridRerankRetriever",
    "tokenize",
]

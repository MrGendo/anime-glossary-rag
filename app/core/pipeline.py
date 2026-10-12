# -*- coding: utf-8 -*-
"""RAG pipeline orchestration: retrieval -> context -> generation -> citation.

This module owns the serving path. It never lets the model invent sources:
citations are resolved against the retrieved hits actually provided."""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from app.generation.answer import AnswerGenerator
from app.generation.llm import LLMClient, MockClient
from app.retrieval.base import Hit, Retriever


class RAGService:
    def __init__(self, retriever: Retriever, llm: Optional[LLMClient] = None,
                 top_k: int = 5, strategy: str = "hybrid"):
        self.retriever = retriever
        self.llm = llm or MockClient()
        self.gen = AnswerGenerator(self.llm)
        self.top_k = top_k
        self.strategy = strategy

    def answer(self, question: str, top_k: Optional[int] = None) -> dict:
        k = top_k or self.top_k
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        t0 = time.time()
        try:
            hits: List[Hit] = self.retriever.search(question, top_k=k)
        except Exception as e:
            return self._error(request_id, f"retrieval_failed: {type(e).__name__}", t0)
        try:
            result = self.gen.generate(question, hits)
        except TimeoutError:
            return self._error(request_id, "llm_timeout", t0)
        except Exception as e:
            return self._error(request_id, f"llm_error: {type(e).__name__}", t0)
        # cited_chunks from the generation layer are already resolved chunk_ids
        # (answer.py maps 【E#】 -> hits[#-1].chunk_id). Attach the label each
        # citation pointed at by re-parsing the answer's 【E#】 markers in order.
        import re as _re
        label_by_cid: dict = {}
        for m in _re.finditer(r"【E(\d+)】", result.answer or ""):
            num = int(m.group(1))
            if 1 <= num <= len(hits):
                cid = hits[num - 1].chunk_id
                label_by_cid.setdefault(cid, f"E{num}")
        citations = []
        for cid in result.cited_chunks:
            h = next((x for x in hits if x.chunk_id == cid), None)
            if h is None:
                continue
            citations.append({
                "label": label_by_cid.get(cid, "E?"),
                "chunk_id": h.chunk_id, "score": h.score,
                "source_id": h.source_id, "page_number": h.page_number,
                "section_title": h.section_title, "snippet": h.text_snippet,
            })
        return {
            "request_id": request_id,
            "question": question,
            "answer": result.answer,
            "refusal": result.refusal,
            "citations": citations,
            "retrieval": [{
                "chunk_id": h.chunk_id, "score": h.score, "method": h.method,
                "source_id": h.source_id, "page_number": h.page_number,
                "section_title": h.section_title, "snippet": h.text_snippet,
            } for h in hits],
            "strategy": self.strategy,
            "top_k": k,
            "model": getattr(self.llm, "model_name", type(self.llm).__name__),
            "latency_ms": int((time.time() - t0) * 1000),
            "ok": True,
            "citation_parse_warning": result.citation_parse_warning,
        }

    @staticmethod
    def _error(request_id: str, error: str, t0: float) -> dict:
        return {
            "request_id": request_id, "ok": False, "error": error,
            "answer": None, "refusal": None, "citations": [], "retrieval": [],
            "latency_ms": int((time.time() - t0) * 1000),
        }

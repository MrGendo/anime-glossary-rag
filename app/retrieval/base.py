"""Abstract retriever interface and the shared Hit model."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, List, Optional

from pydantic import BaseModel, Field

REQUIRED_FIELDS = ("chunk_id", "text")


def iter_jsonl(path) -> Iterator[dict]:
    """Yield non-empty JSON lines from ``path`` (str or Path)."""
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:  # pragma: no cover - defensive
                raise ValueError(f"{path}:{line_no}: invalid JSON: {e}") from e
            if isinstance(obj, dict):
                yield obj


class Hit(BaseModel):
    """One retrieval result. ``score`` semantics depend on ``method``."""

    chunk_id: str
    score: float
    source_id: str = ""
    page_number: Optional[int] = None
    section_title: str = ""
    text_snippet: str = ""
    method: str = "base"


class Retriever(ABC):
    """Base class for all retrievers.

    Subclasses MUST call ``super().__init__(chunks)`` (or set the same
    attributes) so that chunk metadata, snippet generation and ``from_jsonl``
    behave uniformly.
    """

    method: str = "base"

    def __init__(self, chunks: List[dict]):
        seen: set = set()
        self.chunks: List[dict] = []
        for c in chunks:
            if not isinstance(c, dict):
                raise TypeError(f"chunk must be dict, got {type(c).__name__}")
            missing = [f for f in REQUIRED_FIELDS if f not in c or c[f] is None]
            if missing:
                raise ValueError(f"chunk missing required field(s): {missing}")
            cid = str(c["chunk_id"])
            if cid in seen:
                continue  # tolerate duplicate ids, keep first
            seen.add(cid)
            self.chunks.append(c)
        if not self.chunks:
            raise ValueError("chunks must contain at least one item")

    # ------------------------------------------------------------------ api
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Hit]:
        raise NotImplementedError

    def hit_from_index(self, idx: int, score: float, snippet: str = "") -> Hit:
        c = self.chunks[idx]
        if not snippet:
            snippet = self.snippet(c)
        return Hit(
            chunk_id=str(c["chunk_id"]),
            score=float(score),
            source_id=str(c.get("source_id", "") or ""),
            page_number=c.get("page_number"),
            section_title=str(c.get("section_title", "") or ""),
            text_snippet=snippet,
            method=self.method,
        )

    @staticmethod
    def snippet(chunk: dict, width: int = 160) -> str:
        text = str(chunk.get("text", "") or "")
        return text[:width]

    # -------------------------------------------------------------- loaders
    @classmethod
    def from_jsonl(cls, path) -> "Retriever":
        return cls(list(iter_jsonl(path)))

    # ------------------------------------------------------------ utilities
    def __len__(self) -> int:
        return len(self.chunks)

    def _texts(self) -> List[str]:
        return [str(c.get("text", "") or "") for c in self.chunks]

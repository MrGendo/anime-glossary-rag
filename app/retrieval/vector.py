"""Dense vector retriever: sentence-transformers embeddings + FAISS (CPU)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.retrieval.base import Hit, Retriever

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
E5_PREFIX_QUERY = "query: "
E5_PREFIX_DOC = "passage: "

MODEL_FILES = ("model.pkl", "chunks.jsonl", "metadata.json")


def _is_e5(model_name: str) -> bool:
    return "/multilingual-e5" in f"/{model_name}" or "multilingual-e5" in model_name


class VectorRetriever(Retriever):
    """Semantic retriever.

    - Embedding model defaults to a small multilingual model
      (``paraphrase-multilingual-MiniLM-L12-v2``); any sentence-transformers
      model name works, e.g. ``intfloat/multilingual-e5-small`` (query/passages
      prefixes are added automatically for e5-family models).
    - Model weights are downloaded from HuggingFace at construction time.
      If the download fails the error propagates (no silent fallback).
    - ``save(dir)`` / ``load(dir)`` persist the FAISS index, the chunk payload
      and metadata (model name) so reloading needs no re-embedding.
    """

    method = "vector"

    def __init__(
        self,
        chunks: List[dict],
        model_name: str = DEFAULT_MODEL,
        *,
        encode_kwargs: Optional[dict] = None,
        _model=None,
        _index=None,
        _emb=None,
    ):
        super().__init__(chunks)
        self.model_name = model_name
        self.encode_kwargs = dict(encode_kwargs or {})
        if _model is not None and _index is not None and _emb is not None:
            # internal fast path (used by load())
            self._model = _model
            self._index = _index
            self._emb = _emb
            return
        self._lazy_import()
        self._model = self._load_model(model_name)
        self._emb = self._embed(self._texts(), is_query=False)
        self._index = self._build_index(self._emb)

    # ------------------------------------------------------------- imports
    @staticmethod
    def _lazy_import():
        try:
            import faiss  # noqa: F401
            import sentence_transformers  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "VectorRetriever requires 'sentence-transformers' and "
                "'faiss-cpu' (see requirements-app.txt): "
                + str(e)
            ) from e

    @staticmethod
    def _load_model(model_name: str):
        from sentence_transformers import SentenceTransformer

        try:
            return SentenceTransformer(model_name, device="cpu")
        except Exception as e:
            raise RuntimeError(
                f"failed to load/download embedding model '{model_name}' "
                f"from HuggingFace: {e.__class__.__name__}: {e}"
            ) from e

    # ------------------------------------------------------------ encoding
    def _embed(self, texts: List[str], *, is_query: bool) -> "object":
        if _is_e5(self.model_name):
            prefix = E5_PREFIX_QUERY if is_query else E5_PREFIX_DOC
            texts = [prefix + t for t in texts]
        kwargs = {"show_progress_bar": False, "normalize_embeddings": True}
        kwargs.update(self.encode_kwargs)
        return self._model.encode(texts, **kwargs)

    @staticmethod
    def _build_index(emb) -> "object":
        import faiss
        import numpy as np

        mat = np.ascontiguousarray(np.asarray(emb, dtype="float32"))
        if mat.ndim != 2:
            raise ValueError("embeddings must be a 2-D array")
        dim = mat.shape[1]
        index = faiss.IndexFlatIP(dim)  # cosine via L2-normalized vectors
        index.add(mat)
        return index

    # --------------------------------------------------------------- search
    def search(self, query: str, top_k: int = 5) -> List[Hit]:
        if top_k <= 0 or not query.strip():
            return []
        import numpy as np

        qv = np.ascontiguousarray(
            np.asarray(self._embed([query], is_query=True), dtype="float32")
        )
        k = min(max(top_k, 1), self._index.ntotal)
        scores, ids = self._index.search(qv, k)
        hits: List[Hit] = []
        for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
            if idx < 0:
                continue
            hits.append(self.hit_from_index(int(idx), float(score)))
        return hits

    # ---------------------------------------------------------- persistence
    def save(self, dirpath) -> Path:
        """Persist FAISS index + chunk ids + texts + metadata into ``dirpath``."""
        import faiss

        d = Path(dirpath)
        d.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(d / "index.faiss"))
        with open(d / "chunks.jsonl", "w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        meta = {"model_name": self.model_name, "ntotal": self._index.ntotal}
        with open(d / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return d

    @classmethod
    def load(cls, dirpath, model_name: Optional[str] = None) -> "VectorRetriever":
        """Reload a saved index; re-downloads the embedding model for queries."""
        import faiss

        d = Path(dirpath)
        index = faiss.read_index(str(d / "index.faiss"))
        chunks = []
        with open(d / "chunks.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
        name = model_name or meta.get("model_name", DEFAULT_MODEL)
        obj = cls.__new__(cls)
        Retriever.__init__(obj, chunks)
        obj.model_name = name
        obj.encode_kwargs = {}
        obj._model = None
        obj._index = index
        obj._emb = None
        # eager model load (raises on download failure, per spec)
        VectorRetriever._lazy_import()
        obj._model = VectorRetriever._load_model(name)
        return obj

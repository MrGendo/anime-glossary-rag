# -*- coding: utf-8 -*-
"""Client for the vector sidecar: spawns the subprocess lazily and keeps it
alive. Implements the Retriever interface via BM25-score-preserving hybrid:
this class itself is a VECTOR-only retriever (used as hybrid's vector leg)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import List, Optional

from app.retrieval.base import Hit, Retriever

ROOT = Path(__file__).resolve().parents[2]


class SidecarVectorRetriever(Retriever):
    """Vector leg backed by an isolated subprocess (faiss crash containment)."""

    method = "vector_sidecar"

    def __init__(self, chunks: List[dict], index_dir: Optional[str] = None,
                 timeout: float = 30.0):
        super().__init__(chunks)
        self.index_dir = index_dir or str(ROOT / "data/indexes/vector")
        self.timeout = timeout
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._start()

    def _start(self):
        env = dict(os.environ)
        env["VECTOR_INDEX_DIR"] = self.index_dir
        env["OMP_NUM_THREADS"] = "1"
        env["TOKENIZERS_PARALLELISM"] = "false"
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "app.retrieval.vector_sidecar"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, cwd=str(ROOT), env=env)
        # wait for readiness (ping until pong, model load can take seconds)
        import time
        for _ in range(60):
            try:
                if self._rpc({"op": "ping"}).get("pong"):
                    return
            except Exception:
                time.sleep(1.0)
        raise RuntimeError("vector sidecar failed to become ready")

    def _rpc(self, req: dict) -> dict:
        with self._lock:
            if self._proc is None or self._proc.poll() is not None:
                self._start()
            self._proc.stdin.write(json.dumps(req) + "\n")
            self._proc.stdin.flush()
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError("vector sidecar died")
            return json.loads(line)

    def search(self, query: str, top_k: int = 5) -> List[Hit]:
        if top_k <= 0 or not query.strip():
            return []
        out = self._rpc({"op": "search", "query": query, "k": top_k})
        hits: List[Hit] = []
        for idx, score in zip(out.get("ids", []), out.get("scores", [])):
            if idx < 0 or idx >= len(self.chunks):
                continue
            hits.append(self.hit_from_index(int(idx), float(score)))
        return hits

    def close(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


import os  # noqa: E402  (used in _start env)

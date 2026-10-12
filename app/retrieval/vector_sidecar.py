# -*- coding: utf-8 -*-
"""Isolated vector-search sidecar: loads FAISS + MiniLM ONCE in a dedicated
process, serves query embedding + search over a pipe protocol. The API
process talks to it via subprocess stdin/stdout (JSON lines), avoiding the
faiss/loky in-process crash entirely.

Protocol (one JSON per line):
  {"op": "search", "query": "...", "k": 5}  -> {"ids": [...], "scores": [...]}
  {"op": "ping"}                            -> {"pong": true}
"""
import json, os, sys

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

INDEX_DIR = os.environ.get("VECTOR_INDEX_DIR", "data/indexes/vector")

def main():
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer

    meta = json.load(open(f"{INDEX_DIR}/metadata.json"))
    index = faiss.read_index(f"{INDEX_DIR}/index.faiss")
    chunks = [json.loads(l) for l in open(f"{INDEX_DIR}/chunks.jsonl", encoding="utf-8")]
    model = SentenceTransformer(meta["model_name"], device="cpu")
    sys.stderr.write(f"[sidecar] ready: {index.ntotal} vectors, model={meta['model_name']}\n")
    sys.stderr.flush()

    for line in sys.stdin:
        try:
            req = json.loads(line)
        except Exception:
            continue
        op = req.get("op")
        if op == "ping":
            print(json.dumps({"pong": True}), flush=True)
        elif op == "search":
            q = req.get("query", "")
            k = min(int(req.get("k", 5)), index.ntotal)
            qv = model.encode([q], normalize_embeddings=True,
                              show_progress_bar=False).astype("float32")
            qv = np.ascontiguousarray(qv)
            scores, ids = index.search(qv, k)
            print(json.dumps({"ids": [int(i) for i in ids[0]],
                              "scores": [round(float(s), 4) for s in scores[0]]}),
                  flush=True)
        else:
            print(json.dumps({"error": f"unknown op {op}"}), flush=True)

if __name__ == "__main__":
    main()

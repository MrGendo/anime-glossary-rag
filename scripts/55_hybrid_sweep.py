# -*- coding: utf-8 -*-
"""True hybrid eval: BM25 + loaded vector index fused via HybridRetriever.
Sweep alpha on DEV set only (final set stays untouched)."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, sys
sys.path.insert(0, ".")

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]

from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector import VectorRetriever

bm = BM25Retriever(chunks)
vr = VectorRetriever.load("data/indexes/vector")

def metrics(res):
    recs, mrrs, hits = [], [], []
    for q, got in zip(qs, res):
        ev = q["evidence_chunk_ids"]
        if not ev:
            continue
        inter = set(got[:5]) & set(ev)
        recs.append(len(inter)/len(ev))
        rr = next((1.0/(i+1) for i, c in enumerate(got[:5]) if c in ev), 0.0)
        mrrs.append(rr)
        hits.append(1 if inter else 0)
    n = len(recs)
    return {"n": n, "recall@5": round(sum(recs)/n, 4), "mrr@5": round(sum(mrrs)/n, 4),
            "hit@5": round(sum(hits)/n, 4)}

out = {}
for alpha in (0.0, 0.3, 0.5, 0.7, 1.0):
    hy = HybridRetriever(chunks, bm25=bm, vector=vr, alpha=alpha)
    res = [[h.chunk_id for h in hy.search(q["question"], top_k=5)] for q in qs]
    out[f"alpha={alpha}"] = metrics(res)
    print(f"alpha={alpha}", out[f"alpha={alpha}"])

json.dump(out, open("data/eval/results/dev_hybrid_sweep.json", "w"), indent=1)
print("saved")

# -*- coding: utf-8 -*-
"""E group: hybrid(alpha=0.3) + cross-encoder rerank over top-20.
Single process, persisted vector index, guarded model download."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, sys, time
sys.path.insert(0, ".")

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
qs = [json.loads(l) for l in open("data/eval/final_questions.jsonl", encoding="utf-8")]

from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector import VectorRetriever
from app.retrieval.rerank import HybridRerankRetriever

bm = BM25Retriever(chunks)
vr = VectorRetriever.load("data/indexes/vector")
hy = HybridRetriever(chunks, bm25=bm, vector=vr, alpha=0.3)
print("base retrievers ready", flush=True)

try:
    rr = HybridRerankRetriever(chunks, hybrid=hy, rerank_k=20)
    print("rerank retriever constructed", flush=True)
except NotImplementedError as e:
    print("RERANK UNAVAILABLE:", e)
    sys.exit(2)
except Exception as e:
    print("RERANK CONSTRUCT FAILED:", type(e).__name__, str(e)[:200])
    sys.exit(3)

def metrics(res, k=5):
    recs, mrrs, hits = [], [], []
    for q, got in zip(qs, res):
        ev = q["evidence_chunk_ids"]
        if not ev:
            continue
        inter = set(got[:k]) & set(ev)
        recs.append(len(inter)/len(ev))
        rr_ = next((1.0/(i+1) for i, c in enumerate(got[:k]) if c in ev), 0.0)
        mrrs.append(rr_); hits.append(1 if inter else 0)
    n = len(recs)
    return {"n": n, "recall@5": round(sum(recs)/n, 4), "mrr@5": round(sum(mrrs)/n, 4),
            "hit@5": round(sum(hits)/n, 4)}

t0 = time.time()
res = []
for q in qs:
    hits_ = rr.search(q["question"], top_k=5)
    res.append([h.chunk_id for h in hits_])
dt = time.time() - t0
m = metrics(res)
m["latency_avg_ms"] = round(dt/len(qs)*1000, 1)
print("rerank(hybrid a=0.3 + CE):", m, flush=True)

base = json.load(open("data/eval/results/final_retrieval.json"))
print("\nvs hybrid-no-rerank:", {kk: base["hybrid"][kk] for kk in ("recall@5","mrr@5","hit@5")})
out = dict(base)
out["rerank"] = m
json.dump(out, open("data/eval/results/final_retrieval.json", "w"), ensure_ascii=False, indent=1)
print("saved")

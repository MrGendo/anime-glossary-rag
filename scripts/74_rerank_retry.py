# -*- coding: utf-8 -*-
"""E group retry with the correct cross-encoder model id."""
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

rr = HybridRerankRetriever(chunks, hybrid=hy,
                           rerank_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
                           rerank_k=20)
print("constructed", flush=True)

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
res = [[h.chunk_id for h in rr.search(q["question"], top_k=5)] for q in qs]
m = metrics(res)
m["latency_avg_ms"] = round((time.time()-t0)/len(qs)*1000, 1)
print("rerank(ms-marco-CE):", m, flush=True)

base = json.load(open("data/eval/results/final_retrieval.json"))
print("vs hybrid:", {kk: base["hybrid"][kk] for kk in ("recall@5","mrr@5","hit@5")})
out = dict(base); out["rerank"] = m
json.dump(out, open("data/eval/results/final_retrieval.json", "w"), ensure_ascii=False, indent=1)
print("saved")

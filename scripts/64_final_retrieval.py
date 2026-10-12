# -*- coding: utf-8 -*-
"""FINAL test set retrieval comparison (single use, no tuning after this).
Loads persisted vector index separately to dodge the segfault."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, sys, time
sys.path.insert(0, ".")

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
qs = [json.loads(l) for l in open("data/eval/final_questions.jsonl", encoding="utf-8")]

from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever

def metrics(res, k=5):
    recs, mrrs, hits = [], [], []
    per = []
    for q, got in zip(qs, res):
        ev = q["evidence_chunk_ids"]
        if not ev:
            per.append(None); continue
        inter = set(got[:k]) & set(ev)
        rec = len(inter)/len(ev)
        rr = next((1.0/(i+1) for i, c in enumerate(got[:k]) if c in ev), 0.0)
        recs.append(rec); mrrs.append(rr); hits.append(1 if inter else 0)
        per.append({"qid": q["question_id"], "type": q["question_type"],
                    "rec": round(rec, 3), "rr": rr,
                    "got": got[:k], "want": ev})
    n = len(recs)
    # per-type breakdown
    by_type = {}
    for p in per:
        if p is None: continue
        by_type.setdefault(p["type"], []).append(p)
    breakdown = {t: {"n": len(v),
                     "rec": round(sum(x["rec"] for x in v)/len(v), 3),
                     "mrr": round(sum(x["rr"] for x in v)/len(v), 3)}
                 for t, v in by_type.items()}
    return {"n": n, f"recall@{k}": round(sum(recs)/n, 4),
            f"mrr@{k}": round(sum(mrrs)/n, 4),
            f"hit@{k}": round(sum(hits)/n, 4)}, breakdown, per

bm = BM25Retriever(chunks)
t0 = time.time()
res_bm = [[h.chunk_id for h in bm.search(q["question"], top_k=5)] for q in qs]
m_bm, b_bm, per_bm = metrics(res_bm)
m_bm["latency_avg_ms"] = round((time.time()-t0)/len(qs)*1000, 1)
print("bm25 :", m_bm)

from app.retrieval.vector import VectorRetriever
vr = VectorRetriever.load("data/indexes/vector")
t0 = time.time()
res_v = [[h.chunk_id for h in vr.search(q["question"], top_k=5)] for q in qs]
m_v, b_v, per_v = metrics(res_v)
m_v["latency_avg_ms"] = round((time.time()-t0)/len(qs)*1000, 1)
print("vector:", m_v)

hy = HybridRetriever(chunks, bm25=bm, vector=vr, alpha=0.3)
t0 = time.time()
res_h = [[h.chunk_id for h in hy.search(q["question"], top_k=5)] for q in qs]
m_h, b_h, per_h = metrics(res_h)
m_h["latency_avg_ms"] = round((time.time()-t0)/len(qs)*1000, 1)
print("hybrid(a=0.3):", m_h)

print("\nper-type recall (bm25 | vector | hybrid):")
for t in sorted(b_bm):
    print(f"  {t:14s} {b_bm[t]['rec']:.2f} | {b_v.get(t,{}).get('rec',0):.2f} | {b_h.get(t,{}).get('rec',0):.2f}")

out = {"bm25": m_bm, "vector": m_v, "hybrid": m_h,
       "per_type": {"bm25": b_bm, "vector": b_v, "hybrid": b_h},
       "ts": time.strftime("%F %T"), "set": "final60"}
json.dump(out, open("data/eval/results/final_retrieval.json", "w"), ensure_ascii=False, indent=1)
json.dump({"bm25": per_bm, "vector": per_v, "hybrid": per_h},
          open("data/eval/results/final_retrieval_perq.json", "w"), ensure_ascii=False, indent=1)
print("\nsaved final_retrieval.json")

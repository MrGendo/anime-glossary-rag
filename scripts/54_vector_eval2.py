# -*- coding: utf-8 -*-
"""Vector eval v2: load persisted index (no fresh build), pin env, run metrics."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, sys, time
sys.path.insert(0, ".")

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]

from app.retrieval.vector import VectorRetriever
vr = VectorRetriever.load("data/indexes/vector")
print("loaded", vr.model_name, flush=True)

t0 = time.time()
res = [[h.chunk_id for h in vr.search(q["question"], top_k=5)] for q in qs]
dt = time.time() - t0
recs, mrrs, hits = [], [], []
for q, got in zip(qs, res):
    ev = q["evidence_chunk_ids"]
    if not ev:
        continue
    inter = set(got[:5]) & set(ev)
    recs.append(len(inter) / len(ev))
    rr = next((1.0 / (i + 1) for i, c in enumerate(got[:5]) if c in ev), 0.0)
    mrrs.append(rr)
    hits.append(1 if inter else 0)
n = len(recs)
met = {"n": n, "recall@5": round(sum(recs)/n, 4), "mrr@5": round(sum(mrrs)/n, 4),
       "hit@5": round(sum(hits)/n, 4), "latency_avg_ms": round(dt/n*1000, 1)}
print("vector:", met)
json.dump(met, open("data/eval/results/dev_vec_vector_metrics.json", "w"), indent=1)
per_q = [{"qid": q["question_id"], "got": got[:5], "want": q["evidence_chunk_ids"]}
         for q, got in zip(qs, res) if q["evidence_chunk_ids"]]
json.dump(per_q, open("data/eval/results/dev_vec_vector_perq.json", "w"), ensure_ascii=False, indent=1)
print("saved")

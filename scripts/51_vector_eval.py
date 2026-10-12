# -*- coding: utf-8 -*-
"""Vector retrieval standalone: build index (persist), eval recall.
Catches and prints the real exception if any."""
import json, sys, time, traceback
sys.path.insert(0, ".")

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]

from app.retrieval.vector import VectorRetriever

t0 = time.time()
try:
    vr = VectorRetriever(chunks)
    print(f"index built in {time.time()-t0:.1f}s")
except Exception:
    traceback.print_exc()
    sys.exit(1)

try:
    vr.save("data/indexes/vector")
    print("index saved")
except Exception as e:
    print("save failed:", e)

res = [[h.chunk_id for h in vr.search(q["question"], top_k=5)] for q in qs]
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
print(f"vector: n={len(recs)} recall@5={sum(recs)/len(recs):.4f} mrr@5={sum(mrrs)/len(mrrs):.4f} hit@5={sum(hits)/len(hits):.4f}")
per_q = [{"qid": q["question_id"], "got": got[:5]} for q, got in zip(qs, res)]
json.dump(per_q, open("data/eval/results/dev_vec0_vector_perq.json", "w"), ensure_ascii=False, indent=1)
json.dump({"vector": {"n": len(recs), "recall@5": round(sum(recs)/len(recs), 4),
           "mrr@5": round(sum(mrrs)/len(mrrs), 4), "hit@5": round(sum(hits)/len(hits), 4)}},
          open("data/eval/results/dev_vec0_summary.json", "w"), ensure_ascii=False, indent=1)
print("saved")

# -*- coding: utf-8 -*-
"""Smoke test: BM25 retrieval over REAL 620 chunks with dev questions.
Measures Recall@5 for the 20 seed questions (answerable, book-evidence)."""
import json, re, sys
sys.path.insert(0, ".")
from app.retrieval.bm25 import BM25Retriever

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
r = BM25Retriever(chunks)
qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]

hits_n = 0
tot = 0
rows = []
for q in qs:
    if not q["evidence_chunk_ids"]:
        continue
    tot += 1
    got = r.search(q["question"], top_k=5)
    got_ids = [h.chunk_id for h in got]
    inter = set(got_ids) & set(q["evidence_chunk_ids"])
    rec = len(inter) / len(q["evidence_chunk_ids"])
    rows.append((q["question_id"], q["question_type"], rec, got_ids[:3], q["evidence_chunk_ids"]))
    hits_n += 1 if inter else 0

print(f"answerable-with-evidence: {tot} | top5 hit (>=1 evidence): {hits_n} ({hits_n/tot:.0%})")
avg_rec = sum(x[2] for x in rows) / len(rows)
print(f"avg Recall@5: {avg_rec:.2f}")
print("\n== misses (rec<1) ==")
for qid, qt, rec, got, ev in rows:
    if rec < 1:
        print(f"  {qid} {qt} rec={rec:.2f} got={got} want={ev}")

# -*- coding: utf-8 -*-
"""Debug: print exact chunk text for failing anchors to fix quote mismatches.
Anchors must be SUBSTRINGS of actual evidence text. Some fails are because
facts quote a DIFFERENT chunk than mapped (e.g. TD-002 カメラワーク is in
原画 body but maybe spacing broke run). Print evidence texts."""
import json, re

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
by_cid = {c["chunk_id"]: c for c in chunks}
qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]

for s in qs:
    if s["question_id"] not in ("TD-002", "TC-001", "PF-002", "TD-006"):
        continue
    print(f"===== {s['question_id']} evidence =====")
    for cid in s["evidence_chunk_ids"]:
        print(f"--- {cid} ---")
        print(by_cid[cid]["text"][:460])
    print()

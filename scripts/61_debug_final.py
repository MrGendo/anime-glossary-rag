# -*- coding: utf-8 -*-
"""Debug the 12 failing anchors: show what evidence actually contains."""
import json, re

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
by_cid = {c["chunk_id"]: c for c in chunks}
qs = [json.loads(l) for l in open("data/eval/final_questions.jsonl", encoding="utf-8")]
squash = lambda s: re.sub(r"\s+", "", s)

want = {"FD-004", "FD-007", "FD-008", "FD-016", "FD-017", "FC-005", "FC-011",
        "FC-012", "FP-006", "FM-001"}
for s in qs:
    if s["question_id"] not in want:
        continue
    ev = squash(" ".join(by_cid[c]["text"] for c in s["evidence_chunk_ids"]))
    for fact in s["required_facts"]:
        runs = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{6,}", fact)
        for r in runs:
            if squash(r) not in ev:
                probe = squash(r)[:6]
                idx = ev.find(probe)
                ctx = ev[max(0, idx):idx+34] if idx >= 0 else "(not found)"
                print(f"{s['question_id']} '{r[:22]}' -> ev: {ctx}")

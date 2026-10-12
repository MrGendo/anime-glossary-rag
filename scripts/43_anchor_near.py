# -*- coding: utf-8 -*-
"""Check remaining 6 anchors against real text with squash, print near-matches."""
import json, re

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
by_cid = {c["chunk_id"]: c["text"] for c in chunks}
qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]
squash = lambda s: re.sub(r"\s+", "", s)

targets = {"TD-003", "TD-012", "TC-001", "TC-002", "TC-004"}
for s in qs:
    if s["question_id"] not in targets:
        continue
    ev = squash(" ".join(by_cid[c] for c in s["evidence_chunk_ids"]))
    for fact in s["required_facts"]:
        runs = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{6,}", fact)
        for r in runs:
            if squash(r) not in ev:
                # find closest substring in evidence
                probe = squash(r)[:8]
                idx = ev.find(probe)
                print(f"{s['question_id']} RUN '{r[:30]}' -> probe '{probe}' idx={idx}")
                if idx >= 0:
                    print("   evidence has:", ev[idx:idx+40])

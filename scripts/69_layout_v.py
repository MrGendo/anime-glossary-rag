# -*- coding: utf-8 -*-
"""PV-002: quote actual v-chunk text for anchors."""
import json

qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]
chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
vt = {c["chunk_id"]: c["text"] for c in chunks if c["chunk_id"].startswith("v")}

# find layout-related verbatim in v chunks
for c in chunks:
    if c["chunk_id"].startswith("v") and ("layout" in c["text"].lower() or "Layout" in c["text"]):
        i = c["text"].find("ayout")
        print(c["chunk_id"], c["timestamp"], "|", c["text"][max(0,i-20):i+120].replace("\n", " "))

# -*- coding: utf-8 -*-
"""Find which v-chunks actually contain the flow description."""
import json

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
for c in chunks:
    if c["chunk_id"].startswith("v"):
        for kw in ("前期", "中期", "后期", "音乐"):
            if kw in c["text"]:
                print(c["chunk_id"], c["timestamp"], "|", c["text"][:90])
                break

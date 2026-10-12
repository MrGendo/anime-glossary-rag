# -*- coding: utf-8 -*-
"""Search video chunks for layout/布局 keywords (any case)."""
import json

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
for c in chunks:
    if c["chunk_id"].startswith("v"):
        t = c["text"]
        low = t.lower()
        if "layout" in low or "布局" in t or "レイアウト" in t:
            print(c["chunk_id"], c["timestamp"])
            print("  ", t[:180].replace("\n", " "))
        else:
            # print first 60 chars to eyeball content
            print(c["chunk_id"], c["timestamp"], "|", t[:60].replace("\n", " "))

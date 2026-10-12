# -*- coding: utf-8 -*-
"""Find リミテッド chunk: p202 had 'リミテッドアニメーション' + reading on next line
(head and reading on SEPARATE boxes -> our HEAD regex needs same-line reading).
Locate it and check how it was captured."""
import json, re

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
for c in chunks:
    if c["page_number"] in (201, 202, 203) and c["chunk_id"].startswith("g"):
        first = c["text"][:60]
        if "リミテ" in c["text"] or "ループ" in first:
            print(c["chunk_id"], c["section_title"], "p", c["page_number"], "|", c["text"][:120])

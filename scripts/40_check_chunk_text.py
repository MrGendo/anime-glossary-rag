# -*- coding: utf-8 -*-
"""Why do anchors fail? Check the actual chunk text for レイアウト and 動画.
Probably: OCR body text differs slightly (e.g. 酒面設計図 misread) — anchors
must quote the ACTUAL OCR text, not the ideal Japanese."""
import json

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
for c in chunks:
    if c["section_title"] in ("レイアウト", "動画", "動画チェック", "まき直し", "二原"):
        print(f"### {c['chunk_id']} {c['section_title']} (p{c['page_number']})")
        print(c["text"][:420])
        print()

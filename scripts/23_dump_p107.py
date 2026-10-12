# -*- coding: utf-8 -*-
"""Dump ALL text on p107-108 to find 原画/現場 entries (げんが row)."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

for pno in (107, 108):
    print(f"===== p{pno} all boxes (reading order) =====")
    bs = sorted([b for b in pages.get(pno, []) if b["y"] < 0.93],
                key=lambda b: (0 if b["x"] < 0.5 else 1, -b["y"], b["x"]))
    for b in bs:
        print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | {b['text'][:66]}")

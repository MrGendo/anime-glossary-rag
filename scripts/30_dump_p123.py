# -*- coding: utf-8 -*-
"""げ row: 劇場用(げきじょう) p122 col1 bottom → げんが words follow on p123.
Dump p123-p124 heads fully."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

for pno in (123, 124):
    print(f"===== p{pno} FULL =====")
    bs = sorted([b for b in pages.get(pno, []) if b["y"] < 0.93],
                key=lambda b: (0 if b["x"] < 0.5 else 1, -b["y"], b["x"]))
    for b in bs:
        print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | {b['text'][:58]}")
    print()

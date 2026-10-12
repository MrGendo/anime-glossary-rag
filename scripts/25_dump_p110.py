# -*- coding: utf-8 -*-
"""The 原画 headword may be OCR-garbled. Dump the げ-row zone: find 現場 or 原図 entries
then dump surrounding lines. Also brute: dump p110 col0/col1 fully."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

for pno in (109, 110, 111):
    print(f"===== p{pno} =====")
    bs = sorted([b for b in pages.get(pno, []) if b["y"] < 0.93],
                key=lambda b: (0 if b["x"] < 0.5 else 1, -b["y"], b["x"]))
    for b in bs:
        print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | {b['text'][:64]}")
    print()

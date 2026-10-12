# -*- coding: utf-8 -*-
"""p123-124 are illustration pages (組線 explainer), no heads. げ-row continues p125.
Dump p125-126 heads + bare key-term lines."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

HEAD = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・]{1,14})（([ぁ-んァ-ンー・\s]{2,24})）")
for pno in range(125, 129):
    print(f"===== p{pno} =====")
    bs = sorted([b for b in pages.get(pno, []) if b["y"] < 0.93],
                key=lambda b: (0 if b["x"] < 0.5 else 1, -b["y"], b["x"]))
    for b in bs:
        t = b["text"].strip()
        m = HEAD.match(t)
        if m or ("原画" in t and len(t) < 44):
            print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | {t[:56]}")

# -*- coding: utf-8 -*-
"""Inspect chapters 1-3 & 5 page layout: column count heuristic + sample text."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

for pno in [10, 12, 15, 22, 26, 44, 50, 210, 215, 220]:
    boxes = pages.get(pno, [])
    if not boxes:
        print(f"p{pno}: NO BOXES"); continue
    xs = sorted(round(b["x"] + b["w"] / 2, 2) for b in boxes)
    # histogram of x centers
    left = sum(1 for x in xs if x < 0.5); right = len(xs) - left
    print(f"p{pno}: {len(boxes)} boxes | left {left} right {right}")
    boxes_sorted = sorted(boxes, key=lambda b: (-b["y"], b["x"]))
    for b in boxes_sorted[:6]:
        print(f"   y={b['y']:.2f} x={b['x']:.2f} w={b['w']:.2f} | {b['text'][:50]}")

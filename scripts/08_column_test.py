# -*- coding: utf-8 -*-
"""Reconstruct reading order from boxes: split into columns via x histogram.
Glossary pages are 2-column; reconstruct left column top->bottom, then right."""
import json, re

def load(page_no):
    for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
        d = json.loads(line)
        if int(re.search(r"p(\d+)", d["image"]).group(1)) == page_no:
            return d["boxes"]
    return []

def reconstruct(boxes, ncols=2):
    """Split by x center; within column sort by -y then x."""
    cols = [[] for _ in range(ncols)]
    for b in boxes:
        cx = b["x"] + b["w"] / 2
        ci = min(int(cx * ncols), ncols - 1)
        cols[ci].append(b)
    out = []
    for col in cols:
        col.sort(key=lambda b: (-b["y"], b["x"]))
        out.append([b["text"] for b in col])
    return out

for pno in (180, 121, 90):
    boxes = load(pno)
    cols = reconstruct(boxes, 2)
    print(f"===== p{pno}: {len(boxes)} boxes, col0={len(cols[0])}, col1={len(cols[1])} =====")
    for ci, col in enumerate(cols):
        print(f"--- col{ci} first 12 ---")
        for t in col[:12]:
            print("  ", t)

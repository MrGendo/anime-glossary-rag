# -*- coding: utf-8 -*-
"""Locate exact entry-head lines for missing core terms (page-level scan)."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

def show_page_col(pno, contains, label):
    boxes = [b for b in pages.get(pno, []) if b["y"] < 0.93]
    col = [b for b in boxes if contains in b["text"]]
    print(f"== p{pno} {label} ==")
    boxes_sorted = sorted(boxes, key=lambda b: (-b["y"], b["x"]))
    idx = None
    for i, b in enumerate(boxes_sorted):
        if contains in b["text"]:
            idx = i
    if idx is None:
        print("  not found"); return
    for b in boxes_sorted[max(0, idx - 2):idx + 5]:
        print(f"   y={b['y']:.2f} x={b['x']:.2f} | {b['text'][:64]}")

show_page_col(95, "原画（", "原画 head?")
show_page_col(161, "動画検査（", "動画検査 head?")
show_page_col(167, "二原（", "二原 head?")
show_page_col(202, "リミテッドアニメーション", "リミテッド head?")
show_page_col(136, "仕上げ", "仕上げ head?")
show_page_col(134, "作画監督", "作監 already ok")
# also dump all lines on p95 col0 top
print("\n== p95 col0 (x<0.5) top 14 ==")
b0 = sorted([b for b in pages.get(95, []) if b["x"] < 0.5 and b["y"] < 0.93],
            key=lambda b: -b["y"])
for b in b0[:14]:
    print(f"   y={b['y']:.2f} | {b['text'][:64]}")

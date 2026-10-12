# -*- coding: utf-8 -*-
"""Find why 原画/動画検査 etc. are missing: search raw lines for these strings."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

for term in ["原画", "動画検査", "動画マン", "作画", "二原", "ループ", "台本", "仕上げ",
             "美術監督", "リミテッド", "エクスポージャー", "原画マン"]:
    hits = []
    for pno, boxes in pages.items():
        if not (65 <= pno <= 208):
            continue
        for b in boxes:
            if term in b["text"]:
                hits.append((pno, round(b["y"], 2), round(b["x"], 2), b["text"][:60]))
    print(f"== {term}: {len(hits)} box hits ==")
    for h in hits[:4]:
        print("  ", h)

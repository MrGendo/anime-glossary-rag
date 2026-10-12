# -*- coding: utf-8 -*-
"""Search every glossary page for the string げんが in readings and 原画 as head-like
short line ANYWHERE (including p119 col0 bottom or col1)."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

hits = []
for pno, bs in pages.items():
    if not (110 <= pno <= 125):
        continue
    for b in bs:
        t = b["text"].strip()
        if "げんが" in t or ("原画" in t and len(t) <= 20) or "現場（" in t or "げんば" in t:
            hits.append((pno, round(b["y"], 2), round(b["x"], 2), t))
for h in sorted(hits):
    print(h)

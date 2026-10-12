# -*- coding: utf-8 -*-
"""げんが row: 原画 should be right after 現場/検索, around げ-row. Search ALL glossary
pages for lines that start with 原画 and look like heads (short, may lack reading)."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

for pno in range(105, 112):
    bs = pages.get(pno, [])
    for b in bs:
        t = b["text"].strip()
        if re.match(r"^原[画面]", t) or "げんが" in t or "現場（" in t or "原画（" in t:
            print(f"p{pno} y={b['y']:.2f} x={b['x']:.2f} | {t[:60]}")

# also check p94-96 again for 原画 head with different bracket styles
print("---")
for pno in range(93, 97):
    for b in pages.get(pno, []):
        t = b["text"].strip()
        if t.startswith("原画") and len(t) < 30:
            print(f"p{pno} y={b['y']:.2f} x={b['x']:.2f} | {t}")

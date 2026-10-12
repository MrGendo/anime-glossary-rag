# -*- coding: utf-8 -*-
"""p95 does not hold 原画 entry. Search all glossary pages for the head line of 原画.
Gojūon: げ んが would be around げ-row. Check p107-108 (ge-row area)."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

# げんが sorts after げ-row; between 原図(p?) and 現場. Dump col starts p107-109
for pno in (107, 108, 109):
    print(f"===== p{pno} col0 heads =====")
    b0 = sorted([b for b in pages.get(pno, []) if b["x"] < 0.5 and 0.3 < b["y"] < 0.93],
                key=lambda b: -b["y"])
    for b in b0:
        t = b["text"]
        if re.match(r"^[一-龯ぁ-んァ-ーa-zA-Z0-9・]{1,12}（[ぁ-んァ-ンー・\s]+）", t):
            print(f"   y={b['y']:.2f} | {t[:50]}")
    print(f"----- p{pno} col1 heads -----")
    b1 = sorted([b for b in pages.get(pno, []) if b["x"] >= 0.5 and 0.3 < b["y"] < 0.93],
                key=lambda b: -b["y"])
    for b in b1:
        t = b["text"]
        if re.match(r"^[一-龯ぁ-んァ-ーa-zA-Z0-9・]{1,12}（[ぁ-んァ-ンー・\s]+）", t):
            print(f"   y={b['y']:.2f} | {t[:50]}")

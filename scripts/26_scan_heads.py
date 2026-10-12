# -*- coding: utf-8 -*-
"""原画 entry must be in げ-row (after 現場, before 語). Scan p113-116 heads sequence."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

HEAD = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・]{1,14})（([ぁ-んァ-ンー・\s]{2,24})）")
for pno in range(112, 118):
    bs = sorted([b for b in pages.get(pno, []) if b["y"] < 0.93],
                key=lambda b: (0 if b["x"] < 0.5 else 1, -b["y"], b["x"]))
    print(f"===== p{pno} =====")
    for b in bs:
        m = HEAD.match(b["text"].strip())
        if m:
            print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | {b['text'][:48]}")
        elif re.match(r"^(原画|現場|言|誤|五|コ|ゴ)[一-龯ぁ-んァ-ー]{0,4}$", b["text"].strip()):
            print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | BARE: {b['text'][:48]}")

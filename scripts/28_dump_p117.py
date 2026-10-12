# -*- coding: utf-8 -*-
"""き(ki)→ぎ(gi) interleaved: 逆シート(ぎゃく) sits among き row words on p117-118.
So dictionary sorts きゃ<ぎゃ interleaved?? Actually this book sorts dakuten AFTER
the base row block (き row includes きゃくほん..きり..きん, then ぎ row follows).
But 逆シート(ぎゃく) is on p117 BEFORE 脚本(きゃくほん) p118! So book uses
strict gojūon WITH dakuten interleaved (き=gi mixed). That means 原画(げんが) is
between げ-row words... which fall between ぎ(逆バース p117 col0 bottom ~y0.42)
and げ next... Let me dump p117 col1 + p118 col0 fully to find げ row start."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

for pno in (117, 118):
    print(f"===== p{pno} FULL =====")
    bs = sorted([b for b in pages.get(pno, []) if b["y"] < 0.93],
                key=lambda b: (0 if b["x"] < 0.5 else 1, -b["y"], b["x"]))
    for b in bs:
        print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | {b['text'][:58]}")
    print()

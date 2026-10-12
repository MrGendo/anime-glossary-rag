# -*- coding: utf-8 -*-
"""げんが is between 監督(かんとく,p115) and 企画(きかく,p116)? No — げ<か is wrong.
か-row runs p108-117, then が-row interleaved (が Row IS in か section with dakuten).
原画(げ) comes AFTER 監督(かん) and BEFORE 誤/五/コ... Actually gojūon dictionary order:
か(ka) が(ga) き(ki) ぎ(gi) ... so げ(ge) is between ぎ(gi) and こ(ko).
逆バース(ぎゃく) p117 → ぎ row. げ row should follow: 現場→原画→語...
Scan p117-120 full heads."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

HEAD = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・]{1,14})（([ぁ-んァ-ンー・\s]{2,24})）")
for pno in range(117, 121):
    bs = sorted([b for b in pages.get(pno, []) if b["y"] < 0.93],
                key=lambda b: (0 if b["x"] < 0.5 else 1, -b["y"], b["x"]))
    print(f"===== p{pno} =====")
    for b in bs:
        t = b["text"].strip()
        m = HEAD.match(t)
        if m:
            print(f"  c{0 if b['x']<0.5 else 1} y={b['y']:.2f} | {t[:52]}")

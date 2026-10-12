# -*- coding: utf-8 -*-
"""Locate correct chunks for the failing anchors (search all chunk texts)."""
import json, re

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
squash = lambda s: re.sub(r"\s+", "", s)

probes = {
    "FD-004": "トレス台",
    "FD-007": "方向性を指揮",
    "FD-016": "打ち込み）ともいう",
    "FD-017": "シーンごとに描く背景画見本",
    "FC-005": "現場はなにも動かない",
    "FC-011": "連番でつけられた番号",
    "FM-001": "B4サイズ各社専用封",
}
for qid, p in probes.items():
    hits = []
    for c in chunks:
        if squash(p) in squash(c["text"]):
            hits.append(f"{c['chunk_id']}({c['section_title']},p{c['page_number']})")
    print(qid, p, "->", hits[:4])

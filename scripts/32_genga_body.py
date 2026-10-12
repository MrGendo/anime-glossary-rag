# -*- coding: utf-8 -*-
"""Dump full body of 原面（げんが）= 原画 entry (OCR misread) + neighbors p126."""
import json

entries = [json.loads(l) for l in open("data/processed/glossary_full.jsonl", encoding="utf-8")]
for e in entries:
    if e["page"] in (126, 127):
        print(f"### p{e['page']} {e['term']}（{e['reading']}）")
        print(e["body"][:400])
        print()

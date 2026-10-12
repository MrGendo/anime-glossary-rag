"""Locate remaining target terms: 原画, 原画マン, 動画マン, 仕上げ, Layout, げんが."""
import json

with open('data/processed/glossary_full.jsonl') as f:
    entries = [json.loads(l) for l in f]

# find by reading (げんが=原画, どうがまん, げんがまん, しあげ)
for i, e in enumerate(entries, 1):
    t = e['term']
    rd = e['reading']
    if any(k in rd for k in ['げんが', 'どうがまん', 'しあげ', 'れいあうと']) or \
       any(k in t for k in ['原', '仕上', 'Layout', 'LAYOUT', 'レイア']):
        print(f"  g{i:04d} p{e['page']} c{e['col']} | {t} | {rd}")

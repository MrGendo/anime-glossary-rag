# -*- coding: utf-8 -*-
"""Dump specific terms for eval authoring (exact list)."""
import json

entries = [json.loads(l) for l in open("data/processed/glossary_full.jsonl", encoding="utf-8")]
WANT = ["原画", "原画マン", "動画マン", "動画検査", "作画", "二原", "総検", "ループ",
        "リミテッドアニメーション", "台本", "けいこ", "エクスポージャーシート",
        "セルワーク", "トルプ", "担当", "美術監督", "美術ボード", "美術設定", "仕上げ",
        "中割", "都割り", "均等割り", "流れ", "ラフ原", "打ち込み", "色トレス", "仕上検査"]
found = {}
for e in entries:
    t = e["term"].strip()
    if t in WANT and t not in found:
        found[t] = e
for t in WANT:
    if t in found:
        e = found[t]
        print(f"### p{e['page']} {e['term']}（{e['reading']}）")
        print(e["body"][:260]); print()
    else:
        print(f"### {t}: NOT FOUND")

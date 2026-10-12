# -*- coding: utf-8 -*-
"""Dump core 方案A terms with full bodies for eval-set authoring."""
import json, re

entries = [json.loads(l) for l in open("data/processed/glossary_full.jsonl", encoding="utf-8")]

CORE = ["レイアウト", "ラフ", "原画", "原画マン", "動画", "動画マン", "中割り", "中割",
        "動画チェック", "動画検査", "作画", "作画監督", "絵コンテ", "演出", "監督",
        "制作進行", "仕上げ", "撮影", "背景", "美術監督", "クリーンアップ", ".cleanup",
        "二原", "動画総検", "ループ", "リミテッド", "トルク", "台本", "アフレコ",
        "色彩設定", "色指定", "キャラクターデザイン", "メインスタッフ", "担当制作",
        "まき直し", "直し", "太郎", "アップ", "納品", "けいこ", "シート", "タイムシート",
        "エクスポージャー", "セル", "画用紙", " 作画"]

seen = set()
for e in entries:
    t = e["term"].strip()
    if t in seen:
        continue
    for c in CORE:
        if c and (t == c or t.startswith(c) or c in t):
            seen.add(t)
            body = e["body"][:220]
            print(f"### p{e['page']} {e['term']}（{e['reading']}）")
            print(body)
            print()
            break

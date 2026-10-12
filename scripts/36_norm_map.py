# -*- coding: utf-8 -*-
"""Scan glossary for OCR-misread headwords among eval-critical terms:
match by reading (kana) instead of headword. Build norm map."""
import json, re

entries = [json.loads(l) for l in open("data/processed/glossary_full.jsonl", encoding="utf-8")]

# readings of eval-critical terms
WANT = {
    "げんが": "原画", "にげん": "二原", "さくがかんとく": "作画監督",
    "どうが": "動画", "えんしゅつ": "演出", "せいさくしんこう": "制作進行",
    "あたり": "アタリ", "らふ": "ラフ", "おおらふ": "大ラフ",
    "なかわり": "中割り", "どうがちえっく": "動画チェック", "どうがけんさ": "動画検査",
    "くりーんあっぶ": "クリーンアップ", "えこんて": "絵コンテ",
    "まきなおし": "まき直し", "ひきあげ": "引き上げ", "いろしてい": "色指定",
    "しきさいせってい": "色彩設定", "はいけい": "背景", "びじゅつせってい": "美術設定",
    "びかん": "美監", "かんとく": "監督", "さつえい": "撮影",
    "かみせん": "上絵", "いちげん": "一原", "げんず": "原図", "げんとれ": "原トレ",
    "れいあうと": "レイアウト", "たいむしーと": "タイムシート",
    "かっとぶくる": "カット袋", "かっとひょう": "カット表",
    "えんしゅつうち": "演出打ち", "さくだい": "作打ち",
    "しあげけんさ": "仕上検査", "せるけん": "セル検",
    "きゃらひょう": "キャラ表", "さくが": "作画",
}
by_reading = {}
for e in entries:
    r = re.sub(r"[^ぁ-んー]", "", e["reading"])
    by_reading.setdefault(r, []).append(e)

norm = {}
print("== reading-based matches (misread headwords flagged) ==")
for r, canonical in sorted(WANT.items()):
    cands = by_reading.get(r, [])
    if not cands:
        print(f"  {canonical}({r}): NOT FOUND by reading")
        continue
    for e in cands:
        mark = "OK " if e["term"] == canonical or canonical in e["term"] else "MISREAD"
        print(f"  {mark} {canonical} <- p{e['page']} term='{e['term']}' reading='{e['reading']}'")
        norm[e["term"]] = canonical

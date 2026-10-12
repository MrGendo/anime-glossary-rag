# -*- coding: utf-8 -*-
"""Apply anchor corrections (quote exact OCR substrings) to 41_seed_v2.py via
targeted replacements, then regenerate + verify."""
import re

src = open("scripts/41_seed_v2.py", encoding="utf-8").read()

fixes = [
    # TD-012: quote OCR original
    ('"動画作業の済んだカットが原画指示/キャラ表通りか検査",',
     '"動画作業の済んだカットが、原玉の指示通りまたはキャラ表通りに作画されているか",'),
    # TC-001: quote OCR original (酒面/アニメーションの設計図)
    ('"コンテ=ほとんどの情報が書き込まれた設計図（演出绘制）",',
     '"ほとんどの情報が書き込まれたアニメーションの設計図",'),
    ('"LO=絵コンテを元に描き起こされる画面設計図",',
     '"絵コンテを元に描き起こされる酒面設計図のこと（酒面=画面）",'),
    # TC-002: quote OCR originals
    ('"原画=動きのポイント＋画面づくりすべてを計算",',
     '"原画の仕事では、画面構成、カメラワーク、特殊効果、処理方法から画面作りすべてを計算",'),
    ('"動画=原画間を埋める（機械的に埋めるだけではない）"],',
     '"原画と原所の間を機械的に埋めるだけの作来ではなく"],'),
    # TC-004: quote OCR originals
    ('"背景画を描く部署、またはその職種",',
     '"背祭画を描く部署、またはその職種（背祭=背景）",'),
    ('"背景部門では背景と美術とを明確に区別",',
     '"背景部門では背景と美術とを明確に区別しており",'),
]
n = 0
for old, new in fixes:
    if old in src:
        src = src.replace(old, new)
        n += 1
    else:
        print("NOT FOUND:", old[:50])
open("scripts/41_seed_v2.py", "w", encoding="utf-8").write(src)
print("applied", n, "of", len(fixes))

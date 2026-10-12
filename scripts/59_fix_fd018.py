# -*- coding: utf-8 -*-
"""Rewrite FD-018 to be about フル/リミテッド contrast anchored on g0455
(フルアニメーション entry, which mentions the antonym)."""
src = open("scripts/56_final_set.py", encoding="utf-8").read()
old_start = src.find('q("FD-018"')
old_end = src.find('q("FD-019"')
assert old_start > 0 and old_end > old_start
new_q = '''q("FD-018", "フルアニメーション是什么？与リミテッド的关系？",
  "term_def", 2,
  "フルアニメーション是以 1 帧、2 帧拍摄为基本的动画制作方式；リミテッドアニメーション（限制动画，通过减少セル枚数省力化，日本 TV 动画的基础）是它的対語。",
  ["1コマ、2コマを基本とするアニメーション作りのこと",
   "対語（リミテッドアニメーション）"],
  ["フルアニメーション"], notes="リミテッド独立词条的词头与注音跨行未被切分（已知盲区），本题锚定其対語词条。")
'''
src = src[:old_start] + new_q + src[old_end:]
open("scripts/56_final_set.py", "w", encoding="utf-8").write(src)
print("FD-018 rewritten")

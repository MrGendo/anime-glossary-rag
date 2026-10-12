# -*- coding: utf-8 -*-
"""Fix FC-011: カットナンバー head has OCR'd reading なんば一(=ばんばー),
regex missed. Re-anchor on カット表 chunk whose body contains the definition."""
src = open("scripts/56_final_set.py", encoding="utf-8").read()
old = '''  ["カットナンバー", "動画番号"])'''
new = '''  ["カット表", "動画番号"], notes="カットナンバー词条头注音OCR异常（なんば一）未独立成块；其定义句在カット表块正文（絵コンテ作成時に…連番でつけられた番号）。")'''
assert old in src
src = src.replace(old, new)
open("scripts/56_final_set.py", "w", encoding="utf-8").write(src)
print("FC-011 fixed")

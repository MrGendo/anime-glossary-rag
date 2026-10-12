# -*- coding: utf-8 -*-
"""Fix final set: 原撮 has no standalone chunk (merged into 原画 body tail)."""
src = open("scripts/56_final_set.py", encoding="utf-8").read()
fixes = [
    # FD-010 evidence
    ('"原面を撮影して間に合わせる非常手段"],\n  ["原撮"])',
     '"原面を撮影して間に合わせる非常手段"],\n  ["原画"], notes="原撮词条并入原画 chunk（双栏错位），正文含其定义。")'),
    # FP-008 evidence
    ('"まき直し", "引き上げ", "原撮"])',
     '"まき直し", "引き上げ", "原画"])'),
    # FM-006 evidence
    ('"レイアウト撮", "原撮"])',
     '"レイアウト撮", "原画"], notes="原撮定义在原画 chunk 尾部。")'),
]
n = 0
for old, new in fixes:
    if old in src:
        src = src.replace(old, new); n += 1
    else:
        print("NOT FOUND:", old[:60])
open("scripts/56_final_set.py", "w", encoding="utf-8").write(src)
print("applied", n, "of", len(fixes))

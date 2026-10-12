# -*- coding: utf-8 -*-
"""Strong structural validation: gojūon monotonicity check on extracted entries.
The glossary is ordered by kana. If our column reconstruction is correct,
readings must be non-decreasing in gojūon order. Violations = reconstruction
or OCR errors (each gets flagged for manual review list)."""
import json, re

# gojūon order table (a-i-u-e-o rows)
GOJUON = ("あいうえお かきくけこ がぎぐげご さしすせそ ざじずぜぞ たちつてと だぢづでど "
          "なにぬねの はひふへほ ばびぶべぼ ぱぴぷぺぽ まみむめも やゆよ らりるれろ "
          "わをん ぁぃぅぇぉ ゃゅょ ー・").split()
RANK = {c: i for i, c in enumerate(GOJUON)}

def kana_key(reading):
    # convert katakana->hiragana, map unknown to end
    K2H = str.maketrans("ァィゥェォガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポャュョ",
                        "ぁぃぅぇぉがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゃゅょ")
    s = reading.translate(K2H)
    return [RANK.get(c, 99) for c in s]

def leq(a, b):
    return a <= b

entries = [json.loads(l) for l in open("data/processed/glossary_full.jsonl", encoding="utf-8")]
# only entries from glossary pages with clean readings (pure kana)
clean = []
for e in entries:
    r = re.sub(r"[^ぁ-んァ-ンー]", "", e["reading"])
    if r:
        clean.append({**e, "reading_clean": r})

print(f"entries total {len(entries)}, with kana reading {len(clean)}")

violations = []
prev = None
def is_latin(e):
    return bool(re.match(r"^[A-Za-z0-9]", e["term"]))

def sort_key(e):
    if is_latin(e):
        return [0, e["term"].lower()]
    return [1] + kana_key(e["reading_clean"])

for e in clean:
    k = sort_key(e)
    if prev is not None and not leq(prev[0], k):
        violations.append((prev[1], e))
    prev = (k, e)

print("monotonicity violations:", len(violations))
for (a, b) in violations[:20]:
    print(f"  p{a['page']}:{a['term']}（{a['reading']}） -> p{b['page']}:{b['term']}（{b['reading']}）")

# save flagged list for manual review
with open("data/processed/glossary_order_violations.jsonl", "w", encoding="utf-8") as f:
    for a, b in violations:
        f.write(json.dumps({"prev": {k: a[k] for k in ('page','term','reading','y','col')},
                            "next": {k: b[k] for k in ('page','term','reading','y','col')}},
                           ensure_ascii=False) + "\n")
print("saved violations list")

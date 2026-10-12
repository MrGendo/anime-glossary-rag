# -*- coding: utf-8 -*-
"""Full glossary entry extraction: headword + definition body (2-col aware).
Output: data/processed/glossary_full.jsonl
  {term, reading, body, page, col, y}"""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

HEAD = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・]{1,14})(（[ぁ-んァ-ンー・\s]{2,24}）)")

def col_lines(boxes, ncols=2, drop_header=True):
    """Return list of lines per column, merged same-line boxes, reading order."""
    cols = [[] for _ in range(ncols)]
    for b in boxes:
        cx = b["x"] + b["w"] / 2
        ci = min(int(cx * ncols), ncols - 1)
        cols[ci].append(b)
    out = []
    for ci, col in enumerate(cols):
        col.sort(key=lambda b: (-b["y"], b["x"]))
        lines = []
        cur = None
        for b in col:
            if drop_header and b["y"] > 0.93:
                continue
            if cur and abs(cur["y"] - b["y"]) < min(cur["h"], b["h"]) * 0.5:
                cur["text"] += b["text"]
            else:
                if cur: lines.append(cur)
                cur = dict(b)
        if cur: lines.append(cur)
        out.append(lines)
    return out

# reading sequence: col0 (gojūon order) then col1 per page
all_lines = []  # (page, col, idx, line)
for pno in range(65, 209):
    for ci, lines in enumerate(col_lines(pages.get(pno, []), 2)):
        for li, ln in enumerate(lines):
            all_lines.append((pno, ci, li, ln))

# mark heads
entries = []
cur = None
for pno, ci, li, ln in all_lines:
    t = ln["text"].strip()
    m = HEAD.match(t)
    if m and len(m.group(1)) <= 12:
        if cur: entries.append(cur)
        cur = {"term": m.group(1), "reading": m.group(2).strip("（） "),
               "body_lines": [t[m.end():].strip() if m.end() < len(t) else ""],
               "page": pno, "col": ci, "y": round(ln["y"], 3)}
    else:
        if cur is not None:
            cur["body_lines"].append(t)
if cur: entries.append(cur)

for e in entries:
    e["body"] = " ".join(x for x in e["body_lines"] if x)
    e["term_key"] = e["term"]
    del e["body_lines"]

print("entries:", len(entries))
with open("data/processed/glossary_full.jsonl", "w", encoding="utf-8") as f:
    for e in entries:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

# show longest + shortest bodies for sanity
es = sorted(entries, key=lambda e: -len(e["body"]))
print("\n== longest ==")
for e in es[:3]:
    print(e["term"], e["page"], e["body"][:100])
print("\n== shortest ==")
for e in es[-5:]:
    print(e["term"], e["page"], repr(e["body"][:60]))

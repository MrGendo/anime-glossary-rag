# -*- coding: utf-8 -*-
"""Fix glossary entries whose body is empty/short: pull from next lines
even across page/col boundary. Flat reading order across pages."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

HEAD = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・／]{1,20})(（[ぁ-んァ-ンー・\s]{2,24}）)")

def col_lines(boxes, ncols=2):
    cols = [[] for _ in range(ncols)]
    for b in boxes:
        cx = b["x"] + b["w"] / 2
        ci = min(int(cx * ncols), ncols - 1)
        cols[ci].append(b)
    out = []
    for col in cols:
        col.sort(key=lambda b: (-b["y"], b["x"]))
        lines = []
        cur = None
        for b in col:
            if b["y"] > 0.93: continue
            if cur and abs(cur["y"] - b["y"]) < min(cur["h"], b["h"]) * 0.5:
                cur["text"] += b["text"]
            else:
                if cur: lines.append(cur)
                cur = dict(b)
        if cur: lines.append(cur)
        out.append(lines)
    return out

seq = []
for pno in range(65, 209):
    for ci, lines in enumerate(col_lines(pages.get(pno, []), 2)):
        for ln in lines:
            seq.append((pno, ci, ln))

entries = []
cur = None
for i, (pno, ci, ln) in enumerate(seq):
    t = ln["text"].strip()
    m = HEAD.match(t)
    if m and len(m.group(1)) <= 18 and len(t) <= 90:
        if cur: entries.append(cur)
        cur = {"term": m.group(1), "reading": m.group(2).strip("（） "),
               "body_parts": [t[m.end():].strip()], "page": pno, "col": ci,
               "y": round(ln["y"], 3)}
    else:
        if cur is not None:
            cur["body_parts"].append(t)
if cur: entries.append(cur)

for e in entries:
    e["body"] = " ".join(p for p in e["body_parts"] if p)
    e.pop("body_parts")

empty = [e for e in entries if len(e["body"].strip()) < 5]
print("entries:", len(entries), "| near-empty body:", len(empty))
for e in empty[:10]:
    print("  EMPTY:", e["page"], e["term"])

with open("data/processed/glossary_full.jsonl", "w", encoding="utf-8") as f:
    for e in entries:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print("saved", len(entries))

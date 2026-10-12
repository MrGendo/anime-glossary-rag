# -*- coding: utf-8 -*-
"""Parse glossary entries from box OCR (p65-208), 2-column reconstruction.
Entry pattern: headword（reading） at line start (allowing 【】 variants).
Output: data/processed/glossary_entries.jsonl (raw, uncleaned)."""
import json, re, os

os.makedirs("data/processed", exist_ok=True)

# load boxes per page
pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

# entry head pattern: term + （かな reading）
HEAD = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・]{1,12})（([ぁ-んァ-ンー・\s]{2,20})）")

def reconstruct(boxes, ncols=2):
    cols = [[] for _ in range(ncols)]
    for b in boxes:
        cx = b["x"] + b["w"] / 2
        ci = min(int(cx * ncols), ncols - 1)
        cols[ci].append(b)
    lines = []
    for col in cols:
        col.sort(key=lambda b: (-b["y"], b["x"]))
        # merge boxes on same visual line (y overlap > 50% of smaller h)
        cur = None
        for b in col:
            if cur and abs(cur["y"] - b["y"]) < min(cur["h"], b["h"]) * 0.5:
                cur["text"] += b["text"]
            else:
                if cur: lines.append(cur)
                cur = dict(b)
        if cur: lines.append(cur)
    return lines

def page_lines(pno):
    boxes = pages.get(pno, [])
    # header line (chapter title) spans both columns at top -> filter by y>0.9
    boxes = [b for b in boxes if b["y"] < 0.93]
    return reconstruct(boxes, 2)

entries = []
for pno in range(65, 209):
    for ln in page_lines(pno):
        m = HEAD.match(ln["text"])
        if m:
            entries.append({"page": pno, "y": round(ln["y"], 3),
                            "term": m.group(1), "reading": m.group(2),
                            "line": ln["text"]})
print("glossary entry candidates:", len(entries))
# dedupe by (term,page)
seen = set(); uniq = []
for e in entries:
    k = (e["term"], e["page"])
    if k in seen: continue
    seen.add(k); uniq.append(e)
print("after dedupe:", len(uniq))

with open("data/processed/glossary_entries.jsonl", "w", encoding="utf-8") as f:
    for e in uniq:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

# sample spread
for e in uniq[::max(1, len(uniq)//12)][:12]:
    print(e["page"], e["term"], e["reading"])

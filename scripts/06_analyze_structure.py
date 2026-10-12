# -*- coding: utf-8 -*-
"""Analyze OCR results: chapter structure, per-page stats, find glossary range."""
import json, re, collections

pages = []
for line in open("data/raw/ocr_lines.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    text = "\n".join(l["text"] for l in d["lines"])
    pages.append({"page": pno, "text": text, "nlines": len(d["lines"])})
pages.sort(key=lambda x: x["page"])

# find chapter headings
print("== chapter-like headings ==")
pat = re.compile(r"第\s*([0-9０-９]+)\s*[章寮課]")
for p in pages:
    for ln in p["text"].split("\n"):
        if pat.search(ln) and len(ln) < 40:
            print(f"p{p['page']:03d}: {ln}")

# per-page line counts
empty = [p["page"] for p in pages if p["nlines"] == 0 or len(p["text"].strip()) < 10]
print("\n== near-empty pages ==", len(empty), empty[:40])

# glossary candidate: pages where many entries have （かな） pattern
print("\n== glossary density by page (entries with furigana parens) ==")
gloss_pages = []
for p in pages:
    n = len(re.findall(r"（[ぁ-んァ-ンー・\s]+）", p["text"]))
    if n >= 3:
        gloss_pages.append((p["page"], n))
print("glossary-like pages:", len(gloss_pages))
if gloss_pages:
    lo = min(g for g, _ in gloss_pages); hi = max(g for g, _ in gloss_pages)
    print(f"range: p{lo}-p{hi}")

# sample: show glossary entries on a few pages
print("\n== sample entries p121, p180 ==")
for p in pages:
    if p["page"] in (121, 180):
        print(f"--- p{p['page']} ---")
        print(p["text"][:600])

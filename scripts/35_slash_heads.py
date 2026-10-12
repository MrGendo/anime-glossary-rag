# -*- coding: utf-8 -*-
"""p90 アタリ head was 'アタリ／あたり（あたり）' — slash in headword broke the HEAD regex
(character class excludes ／). Find all heads with ／ and count missed entries."""
import json, re

pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

HEAD2 = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・／]{1,20})（([ぁ-んァ-ンー・\s]{2,24})）")
found = []
for pno in range(65, 209):
    for b in pages.get(pno, []):
        if b["y"] > 0.93:
            continue
        t = b["text"].strip()
        m = HEAD2.match(t)
        if m and "／" in m.group(1):
            found.append((pno, t[:40]))
print("slash-containing heads:", len(found))
for f in found[:25]:
    print(f)

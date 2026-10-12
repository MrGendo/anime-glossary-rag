# -*- coding: utf-8 -*-
"""Run box-level OCR over all pages -> data/raw/ocr_boxes.jsonl (resumable)."""
import json, os, subprocess

OUT = "data/raw/ocr_boxes.jsonl"
PAGES = "data/raw/pages_all"
done = set()
if os.path.exists(OUT):
    for line in open(OUT, encoding="utf-8"):
        try:
            done.add(json.loads(line)["image"])
        except Exception:
            pass
pages = sorted(f"{PAGES}/{f}" for f in os.listdir(PAGES) if f.endswith(".png"))
todo = [p for p in pages if p not in done]
print(f"total {len(pages)} done {len(done)} todo {len(todo)}")
CHUNK = 20
for i in range(0, len(todo), CHUNK):
    batch = todo[i:i + CHUNK]
    tmp = "data/raw/ocr_boxes_tmp.jsonl"
    if os.path.exists(tmp):
        os.remove(tmp)
    r = subprocess.run(["swift", "scripts/ocr_boxes.swift", tmp] + batch,
                       capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print("ERR chunk", i, r.stderr[:200]); continue
    with open(OUT, "a", encoding="utf-8") as f, open(tmp, encoding="utf-8") as g:
        f.write(g.read())
    print(f"chunk {i//CHUNK}: +{len(batch)}", flush=True)
print("done ->", OUT)

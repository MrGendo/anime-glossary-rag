# -*- coding: utf-8 -*-
"""Run batch Vision OCR over all rendered pages.
Chunks pages into groups of 20 per swift invocation to bound memory;
appends to data/raw/ocr_lines.jsonl (resumable by skipping done images)."""
import json, os, subprocess, sys

OUT = "data/raw/ocr_lines.jsonl"
PAGES_DIR = "data/raw/pages_all"
done = set()
if os.path.exists(OUT):
    for line in open(OUT, encoding="utf-8"):
        try:
            done.add(json.loads(line)["image"])
        except Exception:
            pass

pages = sorted(f"{PAGES_DIR}/{f}" for f in os.listdir(PAGES_DIR) if f.endswith(".png"))
todo = [p for p in pages if p not in done]
print(f"total {len(pages)}, done {len(done)}, todo {len(todo)}")
if not todo:
    sys.exit(0)

CHUNK = 20
for i in range(0, len(todo), CHUNK):
    batch = todo[i:i + CHUNK]
    tmp = f"data/raw/ocr_tmp.jsonl"
    if os.path.exists(tmp):
        os.remove(tmp)
    r = subprocess.run(["swift", "scripts/ocr_batch.swift", tmp] + batch,
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print("ERR chunk", i, r.stderr[:300])
        continue
    with open(OUT, "a", encoding="utf-8") as f, open(tmp, encoding="utf-8") as g:
        f.write(g.read())
    print(f"chunk {i//CHUNK}: +{len(batch)} (total {i + len(batch)}/{len(todo)})", flush=True)
print("OCR batch complete ->", OUT)

# -*- coding: utf-8 -*-
"""Phase 1 probe: PDF text layer check for アニメ基礎知識大百科.pdf"""
import re, sys, json
from pypdf import PdfReader

PDF = "アニメ基礎知識大百科.pdf"
r = PdfReader(PDF)
n = len(r.pages)
print("pages:", n)
meta = r.metadata
print("metadata:", {k: str(v) for k, v in (meta or {}).items()})

# count text per page
stats = []
empty = 0
total = 0
samples = [0, 1, 5, 20, 60, 110, 160, 200, 220]
for i, p in enumerate(r.pages):
    try:
        t = p.extract_text() or ""
    except Exception as e:
        t = ""
    t2 = re.sub(r"\s+", "", t)
    stats.append(len(t2))
    total += len(t2)
    if not t2:
        empty += 1
    if i in samples:
        print(f"--- page {i+1}: {len(t2)} chars | {t2[:100]!r}")

print(f"TOTAL nonspace chars: {total} | empty pages: {empty}/{n}")
nz = [s for s in stats if s > 0]
print(f"pages with any text: {len(nz)} | median len of those: {sorted(nz)[len(nz)//2] if nz else 0}")

# image inventory on a few pages (scanned check)
try:
    from pypdf import PdfReader as _R
    for pi in [0, 5, 100, 220]:
        pg = r.pages[pi]
        imgs = pg.images if hasattr(pg, "images") else []
        try:
            cnt = len(list(imgs))
            sizes = []
            for im in list(imgs)[:3]:
                sizes.append(getattr(im.image, "size", None))
            print(f"page {pi+1}: {cnt} images, first sizes {sizes}")
        except Exception as e:
            print(f"page {pi+1}: image inspect error {e}")
except Exception as e:
    print("img section err", e)

# fonts (a text PDF would embed fonts)
try:
    seen = set()
    for pi in range(0, n, 40):
        res = r.pages[pi].get("/Resources") or {}
        fonts = res.get("/Font")
        if fonts:
            for k in list(fonts.keys())[:5]:
                f = fonts[k].get_object()
                seen.add(str(f.get("/BaseFont")))
    print("fonts seen (sampled):", sorted(seen)[:10] if seen else "NONE")
except Exception as e:
    print("font err", e)

json.dump({"pages": n, "total_chars": total, "empty_pages": empty,
           "per_page": stats}, open("data/raw/pdf_probe.json", "w"), ensure_ascii=False)
print("saved data/raw/pdf_probe.json")

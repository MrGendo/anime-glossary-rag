# -*- coding: utf-8 -*-
"""Render sample PDF pages to PNG for OCR comparison + set up tessdata dir."""
import fitz  # pymupdf
import os, shutil

PDF = "アニメ基礎知識大百科.pdf"
os.makedirs("data/raw/pages", exist_ok=True)
os.makedirs("data/raw/tessdata", exist_ok=True)

# tessdata dir: symlink homebrew configs + copy langs
src = "/opt/homebrew/share/tessdata"
for f in ["eng.traineddata", "osd.traineddata", "jpn.traineddata"]:
    dst = f"data/raw/tessdata/{f}"
    if f == "jpn.traineddata":
        if not os.path.exists(dst):
            shutil.copy("data/raw/jpn.traineddata", dst)
    else:
        if not os.path.exists(dst):
            os.symlink(f"{src}/{f}", dst)
print("tessdata ready:", os.listdir("data/raw/tessdata"))

doc = fitz.open(PDF)
print("pages:", doc.page_count, "| toc entries:", len(doc.get_toc()))
toc = doc.get_toc()
for t in toc[:30]:
    print("TOC:", t)

# render sample spread across book
samples = [2, 3, 4, 6, 8, 10, 15, 22, 30, 45, 60, 75, 90, 105, 120, 135,
           150, 165, 180, 195, 210, 222]  # 1-based
for pno in samples:
    page = doc[pno - 1]
    # 2x zoom => ~2240x3030, good for small text
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    out = f"data/raw/pages/p{pno:03d}.png"
    pix.save(out)
print("rendered", len(samples), "sample pages at 2x")

# also full-size info of one page
page = doc[10]
print("page 11 rect:", page.rect, "| images:", [i[2:] for i in page.get_images()][:1])

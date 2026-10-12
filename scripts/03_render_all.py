# -*- coding: utf-8 -*-
"""Render ALL 224 pages at 2x zoom for OCR."""
import pymupdf

PDF = "アニメ基礎知識大百科.pdf"
doc = pymupdf.open(PDF)
import os
os.makedirs("data/raw/pages_all", exist_ok=True)
for i in range(doc.page_count):
    pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    pix.save(f"data/raw/pages_all/p{i+1:03d}.png")
print("rendered all", doc.page_count)

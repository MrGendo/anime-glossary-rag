# -*- coding: utf-8 -*-
"""Diagnose BM25 ranking: why c008 beats c001 for query 作画監督."""
import sys
sys.path.insert(0, ".")
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.tokenizer import tokenize

chunks = [
    {"chunk_id": "c001", "text": "作画監督（さくがかんとく）とは、アニメーションの作画の品質を管理する役職である。各話ごとに任命され、原画のチェックと修正を行う。",
     "source_id": "anime_dic", "source_title": "t", "source_type": "book", "page_number": 1,
     "timestamp": None, "section_title": "作画監督", "language": "ja", "extraction_method": "ocr",
     "verification_status": "auto_ok", "extra": {}},
    {"chunk_id": "c008", "text": "作画（さくが）とは絵を描くこと。作画監督、作画監督補、原画、動画などの作画系スタッフの総称でもある。",
     "source_id": "anime_dic", "source_title": "t", "source_type": "book", "page_number": 8,
     "timestamp": None, "section_title": "作画", "language": "ja", "extraction_method": "ocr",
     "verification_status": "auto_ok", "extra": {}},
]
r = BM25Retriever(chunks)
print("q tokens:", tokenize("作画監督"))
for t, cid in [(c["text"], c["chunk_id"]) for c in chunks]:
    print(cid, "tokens:", tokenize(t))
hits = r.search("作画監督", top_k=5)
for h in hits:
    print(h.chunk_id, h.score)

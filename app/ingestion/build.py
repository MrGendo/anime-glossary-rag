# -*- coding: utf-8 -*-
"""Unified chunk assembly (glossary + video + chapters) -> chunks.jsonl.

Mirrors scripts/38 (the executable of record). Kept importable for tests."""
from __future__ import annotations

import json
import re
from typing import Dict, List

from app.ingestion.glossary import extract_glossary_entries, normalize_headword

BOOK_SOURCE = {
    "source_id": "pdf/anime_daihyakka",
    "source_title": "アニメーションの基礎知識大百科（神村幸子）",
    "source_type": "book",
}


def build_chunks(glossary: List[dict], video_chunks: List[dict],
                 chapter_chunks: List[dict]) -> List[dict]:
    """Assemble the unified chunk list with normalization + provenance."""
    out = []
    n_fixed = 0
    for i, e in enumerate(glossary, 1):
        term = e["term"].strip()
        reading = e["reading"].strip()
        canon, fixed = normalize_headword(term, reading)
        term_disp = canon or term
        if fixed:
            n_fixed += 1
        text = (f"{term_disp}（{reading}）: {e['body']}" if e["body"].strip()
                else f"{term_disp}（{reading}）")
        out.append({
            "chunk_id": f"g{i:04d}", "text": text, **BOOK_SOURCE,
            "page_number": e["page"], "timestamp": None,
            "section_title": term_disp, "language": "ja",
            "extraction_method": "vision_ocr",
            "verification_status": "headword_fixed_by_reading" if fixed else "auto_ok",
            "extra": {"term_raw": term, "reading": reading, "col": e.get("col")},
        })
    for v in video_chunks:
        out.append(dict(v))
    for c in chapter_chunks:
        out.append(dict(c))
    return out


def load_pages_boxes(path="data/raw/ocr_boxes.jsonl") -> Dict[int, List[dict]]:
    pages = {}
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        pno = int(re.search(r"p(\d+)", d["image"]).group(1))
        pages[pno] = d["boxes"]
    return pages


def rebuild_glossary(boxes_path="data/raw/ocr_boxes.jsonl") -> List[dict]:
    return extract_glossary_entries(load_pages_boxes(boxes_path))

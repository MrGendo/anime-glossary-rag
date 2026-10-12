# -*- coding: utf-8 -*-
"""Glossary entry extraction + OCR headword normalization.

Mirrors scripts/11 (extraction) and scripts/36 (normalization map)."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

HEAD = re.compile(r"^([一-龯ぁ-んァ-ーa-zA-Z0-9・／]{1,20})（([ぁ-んァ-ンー・\s]{2,24})）")

# canonical name by (hiragana-only) reading; used to fix OCR-misread headwords
NORM_BY_READING: Dict[str, str] = {
    "げんが": "原画", "にげん": "二原", "さくがかんとく": "作画監督",
    "さくが": "作画", "どうが": "動画", "あたり": "アタリ",
    "しあげけんさ": "仕上検査", "どうがけんさ": "動画検査",
}
NORM_BY_TERM = {"原面": "原画", "二豚": "二原", "作画監替": "作画監督",
                "作雨": "作画", "仕上検": "仕上検査"}


def normalize_headword(term: str, reading: str) -> tuple[Optional[str], bool]:
    """Return (canonical_term, was_fixed). canonical=None if no change needed
    beyond identity."""
    hira = re.sub(r"[^ぁ-んー]", "", reading or "")
    canon = NORM_BY_TERM.get(term) or NORM_BY_READING.get(hira)
    if canon and canon != term:
        return canon, True
    return None, False


def extract_glossary_entries(pages_boxes: Dict[int, List[dict]],
                             page_range=range(65, 209)) -> List[dict]:
    """Extract entries {term, reading, body, page, col, y} in flat reading
    order (page by page, column 0 then column 1)."""
    seq = []
    for pno in page_range:
        from app.ingestion.columns import reconstruct_columns
        for ci, lines in enumerate(reconstruct_columns(pages_boxes.get(pno, []), 2)):
            for ln in lines:
                seq.append((pno, ci, ln))

    entries, cur = [], None
    for pno, ci, ln in seq:
        t = ln["text"].strip()
        m = HEAD.match(t)
        if m and len(m.group(1)) <= 18 and len(t) <= 90:
            if cur:
                entries.append(cur)
            cur = {"term": m.group(1), "reading": m.group(2).strip("（） "),
                   "body_parts": [t[m.end():].strip()], "page": pno, "col": ci,
                   "y": round(ln["y"], 3)}
        elif cur is not None:
            cur["body_parts"].append(t)
    if cur:
        entries.append(cur)
    for e in entries:
        e["body"] = " ".join(p for p in e.pop("body_parts") if p)
    return entries

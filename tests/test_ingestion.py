# -*- coding: utf-8 -*-
"""Ingestion package tests: columns, glossary extraction, normalization, build."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

from app.ingestion.columns import reconstruct_columns
from app.ingestion.glossary import extract_glossary_entries, normalize_headword
from app.ingestion.build import build_chunks


def box(x, y, w=0.2, h=0.02, text=""):
    return {"x": x, "y": y, "w": w, "h": h, "text": text}


def test_two_column_reconstruction_order():
    boxes = [
        box(0.1, 0.80, text="B1"), box(0.1, 0.70, text="B2"),   # left col
        box(0.7, 0.85, text="A1"), box(0.7, 0.75, text="A2"),   # right col
        box(0.5, 0.99, text="HEADER"),                            # running head
    ]
    cols = reconstruct_columns(boxes, ncols=2)
    texts = [ln["text"] for ln in cols[0]] + [ln["text"] for ln in cols[1]]
    assert texts == ["B1", "B2", "A1", "A2"]  # header dropped, col0 first


def test_same_line_merge():
    boxes = [box(0.1, 0.5, w=0.15, text="原画（"), box(0.26, 0.5, w=0.15, text="げんが）")]
    cols = reconstruct_columns(boxes, ncols=1)
    assert cols[0][0]["text"] == "原画（げんが）"


def test_normalize_headword_by_reading():
    assert normalize_headword("原面", "げんが") == ("原画", True)
    assert normalize_headword("二豚", "にげん") == ("二原", True)
    assert normalize_headword("作画監督", "さくがかんとく") == (None, False)


def test_extract_entries_and_build_roundtrip(tmp_path):
    boxes = {65: [
        box(0.1, 0.80, w=0.3, text="組（くみ）"), box(0.1, 0.74, w=0.3, text="定義A。"),
        box(0.1, 0.68, w=0.3, text="組線（くみせん）"), box(0.1, 0.62, w=0.3, text="定義B。"),
        box(0.7, 0.80, w=0.3, text="原面（げんが）"), box(0.7, 0.74, w=0.3, text="原画定義。"),
    ]}
    entries = extract_glossary_entries(boxes, page_range=range(65, 66))
    terms = [e["term"] for e in entries]
    assert terms == ["組", "組線", "原面"]
    assert entries[0]["body"] == "定義A。"

    chunks = build_chunks(entries, [], [])
    assert [c["chunk_id"] for c in chunks] == ["g0001", "g0002", "g0003"]
    g3 = chunks[2]
    assert g3["section_title"] == "原画"           # normalized
    assert g3["verification_status"] == "headword_fixed_by_reading"
    assert g3["extra"]["term_raw"] == "原面"
    assert g3["page_number"] == 65


def test_real_glossary_rebuild_count():
    boxes_path = Path(__file__).resolve().parents[1] / "data/raw/ocr_boxes.jsonl"
    if not boxes_path.exists():
        pytest.skip("raw OCR boxes not present")
    entries = extract_glossary_entries_from_path(boxes_path)
    assert len(entries) == 549  # matches pipeline of record


def extract_glossary_entries_from_path(p):
    import json, re
    from app.ingestion.columns import reconstruct_columns as rc
    pages = {}
    for line in open(p, encoding="utf-8"):
        d = json.loads(line)
        pno = int(re.search(r"p(\d+)", d["image"]).group(1))
        pages[pno] = d["boxes"]
    return extract_glossary_entries(pages)

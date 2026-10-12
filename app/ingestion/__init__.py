# -*- coding: utf-8 -*-
"""Ingestion package: OCR reconstruction, glossary entry extraction, chunking.

The runnable pipeline lives in scripts/ (numbered, reproducible). This package
exposes the reusable pieces so app code can import them without shell calls:

- reconstruct_columns: 2-column reading-order reconstruction from Vision boxes
- extract_glossary_entries: headword（reading）entry splitting
- normalize_headword: reading-based canonicalization of OCR-misread headwords
- build_chunks: unified chunks.jsonl assembly (glossary + video + chapters)
"""
from app.ingestion.columns import reconstruct_columns
from app.ingestion.glossary import extract_glossary_entries, normalize_headword
from app.ingestion.build import build_chunks

__all__ = [
    "reconstruct_columns",
    "extract_glossary_entries",
    "normalize_headword",
    "build_chunks",
]

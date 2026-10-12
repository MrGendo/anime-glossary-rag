# -*- coding: utf-8 -*-
"""Reproduce the empty-citations path locally."""
import sys
sys.path.insert(0, ".")
from app.generation.demo_client import ExtractiveDemoClient
from app.generation.answer import AnswerGenerator

class FakeHit:
    def __init__(self, cid, snippet, section):
        self.chunk_id = cid; self.text_snippet = snippet
        self.source_id = "pdf/x"; self.page_number = 202; self.section_title = section

hits = [
    FakeHit("g0534", "レイアウト撮（れいあうとさつ）: アフレコ時までに、最終画魚が完成しないとき、 レイアウトを撮影して問に合わせる非常手段。 【レイアウト】", "レイアウト撮"),
    FakeHit("g0533", "レイアウト（れいあうと）: （LO）とも書く。絵コンテを元に描き起こされる 酒面設計図のこと。", "レイアウト"),
]
gen = AnswerGenerator(ExtractiveDemoClient())
r = gen.generate("レイアウトとは？", hits)
print("answer:", r.answer[:200])
print("cited_chunks:", r.cited_chunks)
print("warning:", r.citation_parse_warning)

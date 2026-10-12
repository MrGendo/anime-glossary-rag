# -*- coding: utf-8 -*-
"""Tests for ExtractiveDemoClient: per-question answers, real citations,
refusal when no evidence."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

from app.generation.demo_client import ExtractiveDemoClient
from app.generation.answer import AnswerGenerator, REFUSAL_ANSWER
from app.generation.prompt import build_messages, build_context


class FakeHit:
    def __init__(self, cid, snippet, source="pdf/anime_daihyakka", page=202,
                 section="レイアウト"):
        self.chunk_id = cid
        self.text_snippet = snippet
        self.source_id = source
        self.page_number = page
        self.section_title = section


def test_different_questions_get_different_answers():
    gen = AnswerGenerator(ExtractiveDemoClient())
    hits_a = [FakeHit("g0533", "レイアウト（れいあうと）: 絵コンテを元に描き起こされる画面設計図のこと。")]
    hits_b = [FakeHit("g0359", "動画（どうが）: 原画と原画の間に中割りを加えていく作業のこと。")]
    ra = gen.generate("レイアウトとは？", hits_a)
    rb = gen.generate("動画とは？", hits_b)
    assert "レイアウト" in ra.answer
    assert "動画" in rb.answer
    assert ra.answer != rb.answer
    assert ra.cited_chunks, "demo answer must cite"


def test_refusal_when_no_evidence():
    gen = AnswerGenerator(ExtractiveDemoClient())
    r = gen.generate("迪士尼流程？", [])
    assert r.refusal is True
    assert "演示模式" in r.answer


def test_answer_declares_demo_mode():
    gen = AnswerGenerator(ExtractiveDemoClient())
    r = gen.generate("中割りとは？", [FakeHit("g0387", "中割り（なかわり）: 原画と原画の間に動画を入れていく作業。")])
    assert "演示模式" in r.answer
    assert "非生成式回答" in r.answer

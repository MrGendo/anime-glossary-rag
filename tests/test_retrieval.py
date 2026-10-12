"""Tests for app/retrieval (BM25 / Vector / Hybrid / Rerank).

The Vector tests need a HuggingFace model download on first run; failures to
import or download are handled gracefully via importorskip / skipif so the
suite stays green offline. The BM25 + Hybrid structure tests MUST pass
regardless of network state.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.retrieval import (  # noqa: E402
    BM25Retriever,
    Hit,
    HybridRerankRetriever,
    HybridRetriever,
    Retriever,
    VectorRetriever,
)
from app.retrieval.tokenizer import tokenize  # noqa: E402

# --------------------------------------------------------------------- data
# 10 hand-made anime-terminology chunks (Japanese glossary style).
CHUNKS = [
    {
        "chunk_id": "c001",
        "text": "作画監督（さくがかんとく）とは、アニメーションの作画の品質を管理する役職である。各話ごとに任命され、原画のチェックと修正を行う。",
        "source_id": "anime_dic_p66",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 66,
        "timestamp": None,
        "section_title": "さ",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c002",
        "text": "セル画（セルが）は、アニメ制作で使われる透明なシートに描かれた画のこと。デジタル化以前の主流の作画技法。",
        "source_id": "anime_dic_p120",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 120,
        "timestamp": None,
        "section_title": "せ",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c003",
        "text": "絵コンテ（えコンテ）は、映像の設計図となる絵付きの脚本。カメラワークや演出意図を指示する。",
        "source_id": "anime_dic_p142",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 142,
        "timestamp": None,
        "section_title": "え",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c004",
        "text": "動画（どうが）は、原画の間の動きを補完する中割りの作業、またはその担当者を指す。動画マンとも呼ばれる。",
        "source_id": "anime_dic_p180",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 180,
        "timestamp": None,
        "section_title": "と",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c005",
        "text": "撮監（さつかん）は撮影監督の略。アニメの撮影処理、光の表現やフィルター効果を統括する役職。",
        "source_id": "anime_dic_p201",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 201,
        "timestamp": None,
        "section_title": "さ",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c006",
        "text": "声優（せいゆう）は、アニメキャラクターの声を演じる俳優。アフレコ（アフターレコーディング）で収録する。",
        "source_id": "anime_dic_p215",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 215,
        "timestamp": None,
        "section_title": "せ",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c007",
        "text": "アイドルアニメとは、アイドル活動を題材にしたアニメのジャンル。ライブシーンの作画と楽曲が重要になる。",
        "source_id": "anime_dic_p230",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 230,
        "timestamp": None,
        "section_title": "あ",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c008",
        "text": "原画（げんが）は、カットの要となる動作のキーとなる絵。原画マンが描き、作画監督のチェックを受ける。",
        "source_id": "anime_dic_p245",
        "source_title": "アニメ基礎知識大百科",
        "source_type": "pdf_ocr",
        "page_number": 245,
        "timestamp": None,
        "section_title": "は",
        "language": "ja",
        "extraction_method": "ocr",
        "verification_status": "verified",
        "extra": {},
    },
    {
        "chunk_id": "c009",
        "text": "アフレコ（アフターレコーディング）は、完成した映像に声を当てて収録すること。声優の演技が映像に合成される。",
        "source_id": "video_bilibili_001",
        "source_title": "アニメ用語解説 動画",
        "source_type": "video_transcript",
        "page_number": None,
        "timestamp": 312.5,
        "section_title": "収録の種類",
        "language": "ja",
        "extraction_method": "whisper",
        "verification_status": "verified",
        "extra": {"video_id": "BV1xx411c7mD"},
    },
    {
        "chunk_id": "c010",
        "text": "制作進行（せいさくしんこう）は、アニメ制作のスケジュールと進捗を管理するスタッフ。现场の調整役である。",
        "source_id": "video_bilibili_002",
        "source_title": "アニメ用語解説 動画",
        "source_type": "video_transcript",
        "page_number": None,
        "timestamp": 645.0,
        "section_title": "制作の裏方",
        "language": "ja",
        "extraction_method": "whisper",
        "verification_status": "verified",
        "extra": {"video_id": "BV1yy811c8mE"},
    },
]


@pytest.fixture()
def chunks():
    return [dict(c) for c in CHUNKS]


@pytest.fixture(scope="module")
def jsonl_path(tmp_path_factory):
    p = tmp_path_factory.mktemp("chunks") / "chunks.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for c in CHUNKS:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return p


# ----------------------------------------------------------------- helpers
def assert_valid_hits(hits, n=None, method=None):
    if n is not None:
        assert len(hits) == n, hits
    for h in hits:
        assert isinstance(h, Hit)
        for field in (
            "chunk_id",
            "score",
            "source_id",
            "page_number",
            "section_title",
            "text_snippet",
            "method",
        ):
            assert field in h.model_fields
        assert h.chunk_id and h.text_snippet
        assert isinstance(h.score, float)
        if method:
            assert h.method == method


def _vector_available() -> tuple[bool, str]:
    try:
        import sentence_transformers  # noqa: F401
        import faiss  # noqa: F401
    except Exception as e:
        return False, f"deps missing: {e}"
    if os.environ.get("RETRIEVAL_SKIP_VECTOR", "").lower() in ("1", "true", "yes"):
        return False, "forced skip via RETRIEVAL_SKIP_VECTOR env"
    return True, ""


VEC_OK, VEC_REASON = _vector_available()
pytestmark_vector = pytest.mark.skipif(not VEC_OK, reason=VEC_REASON)


# ---------------------------------------------------------------- tokenizer
class TestTokenizer:
    def test_japanese_bigram(self):
        assert tokenize("作画監督") == ["作画", "画監", "監督"]

    def test_latin_lowercase_word(self):
        assert tokenize("ACTION CUT") == ["action", "cut"]

    def test_mixed(self):
        toks = tokenize("3DCGアニメ")
        assert "3dcg" in toks
        assert "アニ" in toks and "ニメ" in toks

    def test_kana_runs(self):
        assert "さくが" not in tokenize("さくがかんとく")  # bigram not word
        assert tokenize("さくが") == ["さく", "くが"]


# --------------------------------------------------------------------- bm25
class TestBM25:
    def test_exact_term_ranks_first(self, chunks):
        r = BM25Retriever(chunks)
        hits = r.search("作画監督", top_k=5)
        assert hits, "BM25 returned no hits"
        assert_valid_hits(hits, method="bm25")
        assert hits[0].chunk_id == "c001"
        assert hits[0].score > 0
        # scores sorted desc
        scores = [h.score for h in hits]
        assert scores == sorted(scores, reverse=True)

    def test_exact_latin(self, chunks):
        r = BM25Retriever(chunks)
        hits = r.search("アフレコ", top_k=3)
        assert hits[0].chunk_id == "c009"

    def test_from_jsonl(self, chunks, jsonl_path):
        r = BM25Retriever.from_jsonl(jsonl_path)
        assert len(r) == 10
        assert r.search("絵コンテ", top_k=1)[0].chunk_id == "c003"

    def test_empty_query(self, chunks):
        r = BM25Retriever(chunks)
        assert r.search("", top_k=5) == []
        assert r.search("   ", top_k=5) == []

    def test_top_k_bounds(self, chunks):
        r = BM25Retriever(chunks)
        assert len(r.search("アニメ", top_k=3)) <= 3


# ------------------------------------------------------------------- vector
@pytest.mark.skipif(not VEC_OK, reason=VEC_REASON)
class TestVector:
    @classmethod
    def _make(cls, chunks):
        try:
            return VectorRetriever(chunks)
        except Exception as e:  # model download failure -> skip, not fail
            pytest.skip(f"embedding model unavailable: {e}")

    def test_semantic_top3(self, chunks):
        r = self._make(chunks)
        hits = r.search("アニメの声を演じる人について", top_k=5)
        assert_valid_hits(hits, method="vector")
        top3 = {h.chunk_id for h in hits[:3]}
        assert "c006" in top3, f"voice-actor chunk not in top3: {top3}"

    def test_save_load_roundtrip(self, chunks, tmp_path):
        r = self._make(chunks)
        d = r.save(tmp_path / "vecidx")
        assert (d / "index.faiss").exists()
        assert (d / "chunks.jsonl").exists()
        r2 = VectorRetriever.load(d)
        hits = r2.search("撮影を統括する役職", top_k=3)
        assert_valid_hits(hits, method="vector")
        assert hits[0].chunk_id == "c005"

    def test_from_jsonl(self, jsonl_path):
        try:
            r = VectorRetriever.from_jsonl(jsonl_path)
        except Exception as e:
            pytest.skip(f"embedding model unavailable: {e}")
        assert len(r) == 10


# ------------------------------------------------------------------- hybrid
class TestHybrid:
    def _make(self, chunks, vector=None):
        bm25 = BM25Retriever(chunks)
        return HybridRetriever(chunks, bm25=bm25, vector=vector)

    def test_structure_valid(self, chunks):
        r = self._make(chunks)
        hits = r.search("作画監督の仕事", top_k=5)
        assert 1 <= len(hits) <= 5
        assert_valid_hits(hits, method="hybrid")
        # normalized fused scores within [0, 1]
        for h in hits:
            assert 0.0 <= h.score <= 1.0, h.score
        # desc order
        scores = [h.score for h in hits]
        assert scores == sorted(scores, reverse=True)

    def test_exact_query_top1(self, chunks):
        r = self._make(chunks)
        hits = r.search("作画監督とは", top_k=5)
        assert hits[0].chunk_id == "c001"

    def test_alpha_extremes(self, chunks):
        lex_only = HybridRetriever(chunks, alpha=0.0).search("作画監督", top_k=5)
        assert lex_only and lex_only[0].chunk_id == "c001"

    def test_alpha_validation(self, chunks):
        with pytest.raises(ValueError):
            HybridRetriever(chunks, alpha=1.5)

    def test_missing_vector_leg_ok(self, chunks):
        # vector=None must still work (BM25-only fusion path)
        r = HybridRetriever(chunks, vector=None)
        hits = r.search("原画", top_k=3)
        assert hits and hits[0].chunk_id == "c008"

    @pytest.mark.skipif(not VEC_OK, reason=VEC_REASON)
    def test_full_hybrid(self, chunks):
        try:
            vec = VectorRetriever(chunks)
        except Exception as e:
            pytest.skip(f"embedding model unavailable: {e}")
        r = self._make(chunks, vector=vec)
        hits = r.search("アニメの収録の仕組み", top_k=5)
        assert_valid_hits(hits, method="hybrid")
        assert {h.chunk_id for h in hits[:3]} & {"c009", "c006"}


# ------------------------------------------------------------------- rerank
class TestRerank:
    def test_notimplemented_on_missing_model(self, chunks, monkeypatch, tmp_path):
        """Constructor must raise NotImplementedError when the cross-encoder
        model cannot be loaded (e.g. no network) -> upper layer degrades."""

        import app.retrieval.rerank as rerank_mod

        def _boom(*a, **k):
            raise RuntimeError("simulated download failure")

        monkeypatch.setattr(
            rerank_mod, "DEFAULT_RERANK_MODEL", "nonexistent-model-xyz/zzz"
        )
        # force CrossEncoder load failure
        try:
            from sentence_transformers import CrossEncoder  # noqa: F401

            have_st = True
        except Exception:
            have_st = False
        if have_st:
            import sentence_transformers

            monkeypatch.setattr(
                sentence_transformers, "CrossEncoder", _boom
            )
        with pytest.raises(NotImplementedError):
            HybridRerankRetriever(chunks, rerank_model="nonexistent-model-xyz/zzz")

    @pytest.mark.skipif(not VEC_OK, reason=VEC_REASON)
    def test_rerank_end_to_end(self, chunks):
        try:
            vec = VectorRetriever(chunks)
        except Exception as e:
            pytest.skip(f"embedding model unavailable: {e}")
        hyb = HybridRetriever(chunks, vector=vec)
        try:
            rr = HybridRerankRetriever(chunks, hybrid=hyb)
        except NotImplementedError as e:
            pytest.skip(f"rerank model unavailable: {e}")
        hits = rr.search("絵コンテの役割", top_k=5)
        assert_valid_hits(hits, method="hybrid_rerank")
        assert "c003" in {h.chunk_id for h in hits[:3]}


# -------------------------------------------------------------------- misc
class TestContracts:
    def test_retriever_abc(self):
        with pytest.raises(TypeError):
            Retriever([{"chunk_id": "x", "text": "t"}])  # abstract

    def test_invalid_chunks(self):
        with pytest.raises(ValueError):
            BM25Retriever([])
        with pytest.raises(ValueError):
            BM25Retriever([{"no_id": True}])

    def test_hit_model_fields(self):
        h = Hit(chunk_id="a", score=1.0)
        assert h.method == "base"
        assert h.page_number is None

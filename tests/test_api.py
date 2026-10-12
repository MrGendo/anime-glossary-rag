# -*- coding: utf-8 -*-
"""API smoke tests via TestClient (no live server needed)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["chunks"] > 500
    assert "llm" in d and "strategy" in d


def test_ask_returns_traceable_structure(client):
    r = client.post("/api/ask", json={"question": "レイアウトとは？"})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["request_id"].startswith("req_")
    assert isinstance(d["retrieval"], list) and d["retrieval"]
    hit = d["retrieval"][0]
    for f in ("chunk_id", "score", "method", "source_id", "page_number", "snippet"):
        assert f in hit, f"hit missing {f}"
    # page numbers must be real (within book range)
    assert 1 <= hit["page_number"] <= 224


def test_ask_citations_resolve_to_real_hits(client):
    r = client.post("/api/ask", json={"question": "動画チェックとは？"})
    d = r.json()
    retrieved_ids = {h["chunk_id"] for h in d["retrieval"]}
    for c in d["citations"]:
        assert c["chunk_id"] in retrieved_ids, "citation must reference a retrieved chunk"


def test_ask_empty_question_rejected(client):
    r = client.post("/api/ask", json={"question": ""})
    assert r.status_code == 422


def test_chunk_endpoint(client):
    r = client.get("/api/chunks/g0533")
    assert r.status_code == 200
    c = r.json()
    assert c["chunk_id"] == "g0533"
    assert c["section_title"] == "レイアウト"
    r404 = client.get("/api/chunks/nonexistent")
    assert r404.status_code == 404


def test_frontend_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "动画术语知识库" in r.text
    # API key must never appear in frontend
    assert "ZHIPU_API_KEY" not in r.text

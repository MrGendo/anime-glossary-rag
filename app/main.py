# -*- coding: utf-8 -*-
"""FastAPI service: /api/ask, /api/health, /api/chunks/{id}."""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.core.pipeline import RAGService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anime-rag")

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data/processed/chunks.jsonl"
LOG_DB = ROOT / "data/logs/requests.sqlite"
# Hybrid 向量权重：dev 集 α 扫描选定 0.3（MRR 最优，见 reports/final_report.md §6.1）；
# 与 scripts/64、scripts/81 的实验配置保持一致，可用 RAG_ALPHA 覆盖。
RAG_ALPHA = float(os.environ.get("RAG_ALPHA", "0.3"))

app = FastAPI(title="Anime Glossary RAG", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

_service: RAGService | None = None


def get_service() -> RAGService:
    global _service
    if _service is None:
        chunks = [json.loads(l) for l in open(CHUNKS_PATH, encoding="utf-8")]
        vector = None
        # Vector leg runs in an ISOLATED SUBPROCESS (sidecar): loading faiss +
        # sentence-transformers inside the API process crashed at C level
        # (faiss/loky conflict, final_report §7 case 4). The sidecar keeps the
        # serving process clean while restoring true hybrid retrieval.
        try:
            from app.retrieval.sidecar_client import SidecarVectorRetriever
            vector = SidecarVectorRetriever(chunks)
            log.info("vector sidecar ready (isolated process)")
        except Exception as e:
            vector = None
            log.warning("vector sidecar unavailable (%s); serving BM25-only", e)
        retriever = (HybridRetriever(chunks, vector=vector, alpha=RAG_ALPHA)
                     if vector else BM25Retriever(chunks))
        llm = None
        key = os.environ.get("ZHIPU_API_KEY")
        if key:
            try:
                from app.generation.llm import ZhipuClient
                llm = ZhipuClient(api_key=key, max_retries=4, retry_base_delay=2.0)
                log.info("ZhipuClient ready (retries=4, base_delay=2s)")
            except Exception as e:
                log.warning("Zhipu init failed (%s); falling back to demo mode", e)
        if llm is None:
            from app.generation.demo_client import ExtractiveDemoClient
            llm = ExtractiveDemoClient()
            log.warning("ZHIPU_API_KEY not set -> ExtractiveDemoClient "
                        "(answers are extracted evidence, not model generations)")
        _service = RAGService(retriever, llm)
    return _service


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)


def log_request(rec: dict):
    try:
        LOG_DB.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(LOG_DB)
        con.execute("""CREATE TABLE IF NOT EXISTS requests(
            request_id TEXT PRIMARY KEY, ts TEXT, question TEXT, strategy TEXT,
            hit_chunk_ids TEXT, hit_scores TEXT, answer TEXT, refusal INTEGER,
            cited_chunk_ids TEXT, model TEXT, latency_ms INTEGER,
            ok INTEGER, error TEXT)""")
        con.execute("INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            rec.get("request_id"), time.strftime("%F %T"), rec.get("question"),
            rec.get("strategy"), json.dumps(rec.get("hit_ids", [])),
            json.dumps(rec.get("scores", [])), rec.get("answer"),
            int(bool(rec.get("refusal"))), json.dumps(rec.get("cited_ids", [])),
            rec.get("model"), rec.get("latency_ms"), int(bool(rec.get("ok"))),
            rec.get("error")))
        con.commit()
        con.close()
    except Exception as e:  # observability must never break serving
        log.error("request log failed: %s", e)


@app.get("/api/health")
def health():
    try:
        svc = get_service()
        n = len(svc.retriever)
        return {"status": "ok", "chunks": n,
                "llm": type(svc.llm).__name__, "strategy": svc.strategy}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.post("/api/ask")
def ask(body: AskIn):
    svc = get_service()
    out = svc.answer(body.question)
    log_request({
        "request_id": out.get("request_id"), "question": body.question,
        "strategy": out.get("strategy"),
        "hit_ids": [r["chunk_id"] for r in out.get("retrieval", [])],
        "scores": [r["score"] for r in out.get("retrieval", [])],
        "answer": out.get("answer"), "refusal": out.get("refusal"),
        "cited_ids": [c["chunk_id"] for c in out.get("citations", [])],
        "model": out.get("model"), "latency_ms": out.get("latency_ms"),
        "ok": out.get("ok"), "error": out.get("error"),
    })
    if not out.get("ok"):
        raise HTTPException(status_code=502, detail=out)
    return out


@app.get("/api/chunks/{chunk_id}")
def chunk(chunk_id: str):
    for l in open(CHUNKS_PATH, encoding="utf-8"):
        c = json.loads(l)
        if c["chunk_id"] == chunk_id:
            return c
    raise HTTPException(404, "chunk not found")


app.mount("/", StaticFiles(directory=str(ROOT / "frontend"), html=True), name="static")

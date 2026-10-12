# -*- coding: utf-8 -*-
"""Evaluation runner: controlled comparison of retrieval strategies.

Groups:
  A baseline  : no retrieval (plain LLM)
  B vector    : VectorRetriever
  C bm25      : BM25Retriever
  D hybrid    : HybridRetriever(alpha)
  E rerank    : hybrid + cross-encoder rerank (optional)

Retrieval metrics: Recall@K, MRR@K over evidence_chunk_ids.
Answer metrics (real LLM only): fact coverage, citation accuracy, refusal
correctness, unsupported-claim rate; latency; token usage.

Usage:
  .venv/bin/python scripts/50_run_eval.py --retrieval-only --methods bm25,hybrid
  .venv/bin/python scripts/50_run_eval.py --llm zhipu --methods baseline,hybrid
"""
import argparse, json, os, sys, time
sys.path.insert(0, ".")

from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever

def load_chunks():
    return [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]

def load_questions(split="dev"):
    path = f"data/eval/{split}_questions.jsonl"
    if not os.path.exists(path):
        path = "data/eval/dev_questions.jsonl"
    return [json.loads(l) for l in open(path, encoding="utf-8")]

def retrieval_metrics(res: list, qs: list, k: int = 5):
    """res[i] = list of chunk_ids ranked. Returns recall@k, mrr@k, hit@k.
    Questions with no evidence (refusal-type) are excluded from retrieval
    metrics (nothing to retrieve); they enter answer metrics only."""
    recs, mrrs, hits = [], [], []
    per_q = []
    for q, got in zip(qs, res):
        ev = q["evidence_chunk_ids"]
        if not ev:
            per_q.append(None)
            continue
        got_k = got[:k]
        inter = set(got_k) & set(ev)
        rec = len(inter) / len(ev)
        rr = 0.0
        for rank, cid in enumerate(got_k, 1):
            if cid in ev:
                rr = 1.0 / rank
                break
        recs.append(rec); mrrs.append(rr); hits.append(1 if inter else 0)
        per_q.append({"qid": q["question_id"], "rec": rec, "rr": rr, "got": got_k})
    n = len(recs)
    return {
        "n": n,
        f"recall@{k}": round(sum(recs) / n, 4) if n else None,
        f"mrr@{k}": round(sum(mrrs) / n, 4) if n else None,
        f"hit@{k}": round(sum(hits) / n, 4) if n else None,
    }, per_q

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--methods", default="bm25,hybrid")
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("--llm", default="mock", choices=["mock", "zhipu"])
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--tag", default="run")
    args = ap.parse_args()

    chunks = load_chunks()
    qs = load_questions(args.split)
    print(f"chunks={len(chunks)} questions={len(qs)} methods={args.methods}")

    retrievers = {}
    for m in args.methods.split(","):
        m = m.strip()
        if m == "bm25":
            retrievers[m] = BM25Retriever(chunks)
        elif m == "hybrid":
            try:
                retrievers[m] = HybridRetriever(chunks, alpha=args.alpha)
            except Exception as e:
                print(f"[warn] hybrid unavailable ({e}); skipping")
        elif m == "vector":
            try:
                from app.retrieval.vector import VectorRetriever
                retrievers[m] = VectorRetriever(chunks)
            except Exception as e:
                print(f"[warn] vector unavailable ({e}); skipping")
        elif m in ("baseline", "rerank"):
            pass
        else:
            print(f"[warn] unknown method {m}")

    os.makedirs("data/eval/results", exist_ok=True)
    summary = {"tag": args.tag, "split": args.split, "ts": time.strftime("%F %T"),
               "n_questions": len(qs), "topk": args.topk}
    for name, r in retrievers.items():
        t0 = time.time()
        res = [[h.chunk_id for h in r.search(q["question"], top_k=args.topk)] for q in qs]
        dt = time.time() - t0
        met, per_q = retrieval_metrics(res, qs, k=args.topk)
        met["latency_total_s"] = round(dt, 2)
        met["latency_avg_ms"] = round(dt / max(1, len(qs)) * 1000, 1)
        summary[name] = met
        with open(f"data/eval/results/{args.tag}_{name}_perq.json", "w", encoding="utf-8") as f:
            json.dump(per_q, f, ensure_ascii=False, indent=1)
        print(name, met)

    with open(f"data/eval/results/{args.tag}_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print("saved summary")

if __name__ == "__main__":
    main()

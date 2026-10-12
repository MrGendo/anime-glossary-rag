# -*- coding: utf-8 -*-
"""FINAL answer-level comparison: A baseline (no retrieval) vs D hybrid RAG.

Design:
- Same question set (final 60), same model (glm-4-flash), same generation
  params; A gets NO evidence (no_rag mode), D gets hybrid(alpha=0.3) top-5.
- Grading: deterministic fact-coverage grader (string/fuzzy match of each
  required_fact's Japanese anchor against the answer, whitespace-insensitive,
  OCR-variant tolerant) + refusal correctness for unanswerable questions.
  No LLM-judge by default (small set -> explainable rule-based scoring);
  raw answers saved for manual/LLM re-review.
- Metrics: fact coverage (covered/total facts), full-fact rate (all facts of
  a question covered), refusal accuracy (refused / should-refuse), citation
  validity (RAG only: cited chunk in evidence set), latency, tokens.
Outputs: data/eval/results/final_answers_{A,D}.jsonl + answer_metrics.json
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, re, sys, time
sys.path.insert(0, ".")

key = [l.strip().split("=", 1)[1] for l in open(".env") if l.startswith("ZHIPU_API_KEY=")][0]
os.environ["ZHIPU_API_KEY"] = key

from app.generation.llm import ZhipuClient
from app.generation.prompt import build_messages, build_context
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector import VectorRetriever

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
qs = [json.loads(l) for l in open("data/eval/final_questions.jsonl", encoding="utf-8")]

llm = ZhipuClient(api_key=key)
bm = BM25Retriever(chunks)
vr = VectorRetriever.load("data/indexes/vector")
hy = HybridRetriever(chunks, bm25=bm, vector=vr, alpha=0.3)

# ---- OCR-variant-tolerant matcher ----
VARIANTS = {"画面": ["酒面", "画面"], "背景": ["背界", "背祭", "背環", "背景", "背無"],
            "原画": ["原面", "原所", "原囲", "原由", "原玉", "原画"],
            "検査": ["検奮", "検査"], "産業": ["産来", "産業"], "法則": ["法期", "法則"],
            "作業": ["作来", "作楽", "作薬", "作業"], "撮影": ["採影", "提影", "撮影", "撮誌"],
            "声優": ["声優"], "動画": ["動面", "動由", "動囲", "動画", "動治"],
            "紙": ["結", "紙"], "封筒": ["封間", "封筒"], "職種": ["厳種", "栽種", "取種", "職種"],
            "監督": ["監替", "監証", "監督"], "演技": ["満技", "訓技", "演技"],
            "台本": ["台本"], "方向性": ["方肉性", "方向性"], "決まり": ["決まり"],
            "間隔": ["期隔", "間隔"], "絶滅": ["絶話", "絶滅"], "状態": ["状窓", "状態"],
            "様子を見る": ["様子を見る"]}

def variants_of(term):
    for canon, vs in VARIANTS.items():
        if term == canon or term in canon:
            return vs
    return [term]

def fact_covered(fact, answer):
    """A fact is covered if (a) its Japanese anchor (>=6 chars) appears in the
    answer modulo whitespace + OCR variants, or (b) >=2 of its shorter runs
    appear (partial credit threshold for contrast-type facts)."""
    a = re.sub(r"\s+", "", answer or "")
    runs = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{4,}", fact)
    if not runs:
        # Chinese-language fact (video/refusal criteria): substring check
        core = re.sub(r"[^\u4e00-\u9fffぁ-んァ-ンA-Za-z0-9]", "", fact)
        return core[:8] in a if len(core) >= 8 else False
    strong = 0
    for r in runs:
        hit = any(v + r[len(canon_v):] if r.startswith(canon_v) else v in a
                  for canon_v in [r] for v in variants_of(r))
        # simpler: check each variant substitution on the full run
        hit = False
        for canon, vs in VARIANTS.items():
            if canon in r:
                for v in vs:
                    if v + r.replace(canon, "", 1) and re.sub(r"\s+", "", v + r.split(canon, 1)[1] if canon in r else "") in a:
                        hit = True; break
                if hit: break
        if not hit and re.sub(r"\s+", "", r) in a:
            hit = True
        strong += 1 if hit else 0
    return strong >= 1 and strong / len(runs) >= 0.5

def run_group(group, out_path):
    results = []
    tot_facts = covered_facts = 0
    full_fact_q = 0
    answerable_q = 0
    should_refuse = refused_ok = 0
    cited_valid = cited_total = 0
    latencies = []
    tokens = {"prompt": 0, "completion": 0}
    for q in qs:
        question = q["question"]
        t0 = time.time()
        if group == "D":
            hits = hy.search(question, top_k=5)
            context = build_context(hits)
            messages = build_messages(question, context, mode="rag")
        else:
            hits = []
            messages = build_messages(question, "", mode="no_rag")
        try:
            resp = llm.chat(messages)
            answer = resp.text
            usage = {"prompt": resp.usage.prompt_tokens, "completion": resp.usage.completion_tokens}
        except Exception as e:
            answer = f"__LLM_ERROR__ {type(e).__name__}"
            usage = {"prompt": 0, "completion": 0}
        lat = time.time() - t0
        latencies.append(lat)
        tokens["prompt"] += usage["prompt"]
        tokens["completion"] += usage["completion"]

        refusal = ("证据不足" in answer) or answer.strip().startswith(("不知道", "抱歉", "对不起", "无法回答"))
        if q["answerable"]:
            answerable_q += 1
            nf = len(q["required_facts"])
            nc = sum(1 for f in q["required_facts"] if fact_covered(f, answer))
            tot_facts += nf; covered_facts += nc
            if nc == nf:
                full_fact_q += 1
        else:
            should_refuse += 1
            if refusal:
                refused_ok += 1
        # citation validity (D only)
        cite_labels = re.findall(r"【E(\d+)】", answer)
        if group == "D" and hits:
            hit_ids = {h.chunk_id for h in hits}
            ev_ids = set(q["evidence_chunk_ids"])
            for lab in cite_labels:
                i = int(lab) - 1
                cited_total += 1
                if 0 <= i < len(hits) and hits[i].chunk_id in ev_ids:
                    cited_valid += 1
        results.append({
            "question_id": q["question_id"], "type": q["question_type"],
            "answerable": q["answerable"], "answer": answer, "refusal": refusal,
            "latency_s": round(lat, 2),
            "facts_covered": (nc if q["answerable"] else None),
            "facts_total": (nf if q["answerable"] else None),
            "citations": cite_labels,
            "retrieved": [h.chunk_id for h in hits][:5],
        })
        print(f"[{group}] {q['question_id']} ans={q['answerable']} "
              f"cover={nc if q['answerable'] else '-'}/{nf if q['answerable'] else '-'} "
              f"refusal={refusal} {lat:.1f}s", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    met = {
        "group": group, "n_questions": len(qs), "answerable": answerable_q,
        "fact_coverage": round(covered_facts / tot_facts, 4) if tot_facts else None,
        "full_fact_rate": round(full_fact_q / answerable_q, 4) if answerable_q else None,
        "refusal_accuracy": round(refused_ok / should_refuse, 4) if should_refuse else None,
        "citation_validity": round(cited_valid / cited_total, 4) if cited_total else None,
        "avg_latency_s": round(sum(latencies) / len(latencies), 2),
        "tokens": dict(tokens),
    }
    return met

print("=== Group A: baseline (no retrieval) ===")
mA = run_group("A", "data/eval/results/final_answers_A.jsonl")
print(json.dumps(mA, ensure_ascii=False))
print("\n=== Group D: hybrid RAG ===")
mD = run_group("D", "data/eval/results/final_answers_D.jsonl")
print(json.dumps(mD, ensure_ascii=False))

json.dump({"A": mA, "D": mD, "ts": time.strftime("%F %T"),
           "model": "glm-4-flash"},
          open("data/eval/results/answer_metrics.json", "w"), ensure_ascii=False, indent=1)
print("\nsaved answer_metrics.json")

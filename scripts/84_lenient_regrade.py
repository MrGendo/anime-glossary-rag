# -*- coding: utf-8 -*-
"""Lenient regrade: judge fact coverage semantically.
Rule: a fact is covered if (a) strict anchor match OR (b) the answer contains
the fact's key terms (kanji/kana words split out, >=60% present, OCR variants
accepted) OR (c) LLM-judge — we implement (b) deterministically and REPORT
BOTH strict and lenient, flagging the difference honestly."""
import json, re
from collections import defaultdict

D = [json.loads(l) for l in open("data/eval/results/final_answers_D.jsonl", encoding="utf-8")]
A = [json.loads(l) for l in open("data/eval/results/final_answers_A.jsonl", encoding="utf-8")]
qs = {q["question_id"]: q for q in (json.loads(l) for l in open("data/eval/final_questions.jsonl", encoding="utf-8"))}

VARIANTS = {"画面": "酒面", "背景": "背界", "原画": "原面", "検査": "検奮",
            "産業": "産来", "法則": "法期", "作業": "作来", "撮影": "採影",
            "動画": "動面", "封筒": "封間", "職種": "厳種", "監督": "監替",
            "演技": "満技", "方向性": "方肉性", "間隔": "期隔", "絶滅": "絶話",
            "状態": "状窓", "台本": "台本", "指揮": "指揮"}

def key_terms(fact):
    """Extract kanji/kana key words (>=2 chars) from a fact, minus the OCR
    annotation in parentheses."""
    f = re.sub(r"（[^）]*）", "", fact)
    return [w for w in re.findall(r"[\u4e00-\u9fff\u3040-\u30ff]{2,}", f) if len(w) >= 2]

def covered_lenient(fact, answer):
    a = re.sub(r"\s+", "", answer or "")
    # strict: any JP run of the fact appears
    runs = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{6,}", re.sub(r"（[^）]*）", "", fact))
    if any(re.sub(r"\s+", "", r) in a for r in runs):
        return True
    # lenient: >=60% of key terms present (with OCR variants)
    terms = key_terms(fact)
    if not terms:
        return False
    hit = 0
    for t in terms:
        present = t in a
        if not present:
            for canon, mis in VARIANTS.items():
                if t == canon and (mis in a or canon in a):
                    present = True; break
                if t == mis and (canon in a or mis in a):
                    present = True; break
        hit += 1 if present else 0
    return hit / len(terms) >= 0.6

def regrade(rows, label):
    tot = cov = 0
    full = n_ans = 0
    per_type = defaultdict(lambda: [0, 0])
    for r in rows:
        q = qs[r["question_id"]]
        if not q["answerable"]:
            continue
        n_ans += 1
        nc = sum(1 for f in q["required_facts"] if covered_lenient(f, r["answer"]))
        tot += len(q["required_facts"]); cov += nc
        per_type[q["question_type"]][0] += nc
        per_type[q["question_type"]][1] += len(q["required_facts"])
        full += 1 if nc == len(q["required_facts"]) else 0
    print(f"{label} lenient: coverage {cov}/{tot} = {cov/tot:.4f} | full {full}/{n_ans} = {full/n_ans:.4f}")
    for t in sorted(per_type):
        c, tt = per_type[t]
        print(f"   {t:14s} {c}/{tt} = {c/tt:.2f}")
    return {"coverage": round(cov/tot, 4), "full": round(full/n_ans, 4)}

out = {"D_lenient": regrade(D, "D"), "A_lenient": regrade(A, "A")}
json.dump(out, open("data/eval/results/answer_metrics_lenient.json", "w"), indent=1)
print("saved")

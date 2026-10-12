# -*- coding: utf-8 -*-
"""Analyze answer-level results: per-type breakdown, worst cases, sample answers."""
import json
from collections import defaultdict

A = [json.loads(l) for l in open("data/eval/results/final_answers_A.jsonl", encoding="utf-8")]
D = [json.loads(l) for l in open("data/eval/results/final_answers_D.jsonl", encoding="utf-8")]
qs = {q["question_id"]: q for q in (json.loads(l) for l in open("data/eval/final_questions.jsonl", encoding="utf-8"))}

def by_type(rows, label):
    agg = defaultdict(lambda: [0, 0, 0, 0])  # covered, total, full, n_ans
    ref = [0, 0]
    for r in rows:
        t = r["type"]
        if r["answerable"]:
            agg[t][0] += r["facts_covered"]; agg[t][1] += r["facts_total"]
            agg[t][2] += 1 if r["facts_covered"] == r["facts_total"] else 0
            agg[t][3] += 1
        else:
            ref[0] += 1 if r["refusal"] else 0; ref[1] += 1
    print(f"== {label} per-type coverage ==")
    for t in sorted(agg):
        c, tot, full, n = agg[t]
        print(f"  {t:14s} {c}/{tot} = {c/tot:.2f} | full {full}/{n}")
    print(f"  refusal: {ref[0]}/{ref[1]}")

by_type(A, "A")
by_type(D, "D")

# biggest per-question deltas
print("\n== largest improvements (D vs A) ==")
deltas = []
for a, d in zip(A, D):
    if a["answerable"] and a["facts_total"]:
        da = a["facts_covered"] / a["facts_total"]
        dd = d["facts_covered"] / d["facts_total"]
        deltas.append((dd - da, a["question_id"], a["type"], f"{da:.2f}->{dd:.2f}"))
deltas.sort(reverse=True)
for x in deltas[:8]:
    print("  ", x)

print("\n== D group unanswered-but-should (cover=0) ==")
for d in D:
    if d["answerable"] and d["facts_covered"] == 0:
        print(f"  {d['question_id']} {d['type']} refusal={d['refusal']} retrieved={d['retrieved'][:3]} want={qs[d['question_id']]['evidence_chunk_ids'][:3]}")

# sample D answer for the report
print("\n== sample D answer (TD-quality) ==")
for d in D:
    if d["question_id"] == "FD-014":
        print(d["answer"][:350])

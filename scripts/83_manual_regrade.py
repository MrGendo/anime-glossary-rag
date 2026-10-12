# -*- coding: utf-8 -*-
"""Manual-regrade sample: D-group cover=0 questions whose evidence WAS retrieved.
Print answer vs facts for human judgment (report both strict & lenient numbers)."""
import json

D = [json.loads(l) for l in open("data/eval/results/final_answers_D.jsonl", encoding="utf-8")]
qs = {q["question_id"]: q for q in (json.loads(l) for l in open("data/eval/final_questions.jsonl", encoding="utf-8"))}

SAMPLE = ["FD-006", "FD-014", "FD-015", "FC-001", "FP-004", "FD-022"]
for d in D:
    if d["question_id"] not in SAMPLE:
        continue
    q = qs[d["question_id"]]
    print(f"===== {d['question_id']} ({d['type']}) | retrieved {d['retrieved'][:3]} | want {q['evidence_chunk_ids']}")
    print("FACTS:")
    for f in q["required_facts"]:
        print("  -", f[:90])
    print("ANSWER:")
    print(" ", d["answer"][:400].replace("\n", " "))
    print()

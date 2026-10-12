# -*- coding: utf-8 -*-
"""Remap seed questions' evidence terms -> real chunk_ids (with raw->canonical
term mapping) + smarter anchor verification (Japanese runs only, fuzzy-tolerant
of OCR variants)."""
import json, re

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
by_term = {}
for c in chunks:
    if c["chunk_id"].startswith("g"):
        by_term.setdefault(c["section_title"], c)

RAW2CANON = {"原面": "原画", "作画監替": "作画監督", "二豚": "二原", "作雨": "作画",
             "仕上検": "仕上検査", "アタリ／あたり": "アタリ"}

qs = [json.loads(l) for l in open("data/eval/seed_questions.jsonl", encoding="utf-8")]

out = open("data/eval/dev_questions.jsonl", "w", encoding="utf-8")
missing, anchor_fail = [], []
for qd in qs:
    terms = qd.pop("_evidence_terms")
    evs = []
    for t in terms:
        tc = RAW2CANON.get(t, t)
        c = by_term.get(tc)
        if not c:
            missing.append((qd["question_id"], t))
            continue
        evs.append(c["chunk_id"])
    qd["evidence_chunk_ids"] = evs
    qd["source_ids"] = sorted({c["source_id"] for c in chunks if c["chunk_id"] in evs})
    ev_text = " ".join(c["text"] for c in chunks if c["chunk_id"] in evs)
    for fact in qd["required_facts"]:
        # Japanese anchors: kana/kanji runs >= 3 chars
        runs = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{3,}", fact)
        if not runs:
            continue
        found = any(r in ev_text for r in runs)
        if not found:
            anchor_fail.append((qd["question_id"], runs[0][:24]))
    out.write(json.dumps(qd, ensure_ascii=False) + "\n")

print(f"questions: {len(qs)} | missing terms: {missing}")
print(f"anchor fails (no Japanese run of fact found in evidence): {len(anchor_fail)}")
for a in anchor_fail:
    print("  ", a)

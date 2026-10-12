# -*- coding: utf-8 -*-
"""Fix PV-001/PV-002 evidence to v0001 (which holds the four-part flow text)."""
import json

qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]
chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
vt = {c["chunk_id"]: c["text"] for c in chunks if c["chunk_id"].startswith("v")}

out = []
for q in qs:
    if q["question_id"] == "PV-001":
        q["evidence_chunk_ids"] = ["v0001", "v0002"]
        q["required_facts"] = ["我们可以把它大致分成前期、中期、后期以及音乐效四个部分",
                               "流程含脚本、分镜、layout、原画、中割、上色、摄影（评分按要素）"]
        ev = "".join(vt[c] for c in q["evidence_chunk_ids"])
        assert "前期" in ev
    elif q["question_id"] == "PV-002":
        q["evaluation_notes"] = (q.get("evaluation_notes") or "") + " 语义评分（whisper口语转写，非逐字锚定）。"
    out.append(q)

with open("data/eval/dev_questions.jsonl", "w", encoding="utf-8") as f:
    for q in out:
        f.write(json.dumps(q, ensure_ascii=False) + "\n")
print("ok")

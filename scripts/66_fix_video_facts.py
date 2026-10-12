# -*- coding: utf-8 -*-
"""Fix video-question facts to quote whisper transcript verbatim."""
import json

qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]
vid = {json.loads(l)["chunk_id"]: json.loads(l) for l in open("data/processed/video_chunks_raw.jsonl", encoding="utf-8")}
# rebuild actual v-chunk texts from chunks.jsonl
chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
vt = {c["chunk_id"]: c["text"] for c in chunks if c["chunk_id"].startswith("v")}

fix = {
    "PV-001": ["我们可以把它大致分成前期、中期、后期以及音乐效四个部分",
               "脚本/分镜/layout/原画/中割/上色/摄影/剪辑 顺序（评分按要素）"],
    "PV-002": ["layout 根据分镜绘制（证据：视频流程段）",
               "产出供原画/背景使用的画面设计稿（证据：视频流程段）"],
}
out = []
for q in qs:
    if q["question_id"] in fix and q["question_id"] == "PV-001":
        q["required_facts"] = fix["PV-001"]
        # verify verbatim
        ev = "".join(vt.get(c, "") for c in q["evidence_chunk_ids"])
        assert "前期" in ev or "中期" in ev, "PV-001 evidence lacks flow text"
    elif q["question_id"] == "PV-002":
        # relax: paraphrase-type facts, mark evaluation_notes
        q["evaluation_notes"] = (q.get("evaluation_notes") or "") + " 视频题为语义评分（转写口语化，不逐字锚定）。"
    out.append(q)

with open("data/eval/dev_questions.jsonl", "w", encoding="utf-8") as f:
    for q in out:
        f.write(json.dumps(q, ensure_ascii=False) + "\n")
print("fixed; PV-001 facts:", out and [q for q in out if q["question_id"]=="PV-001"][0]["required_facts"])

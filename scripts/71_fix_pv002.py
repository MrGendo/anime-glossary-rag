# -*- coding: utf-8 -*-
"""PV-002 final fix: anchor on v0004 (Lightout=layout whisper variant)."""
import json

qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]

out = []
for q in qs:
    if q["question_id"] == "PV-002":
        q["evidence_chunk_ids"] = ["v0004", "v0005"]
        q["required_facts"] = [
            "需要用标准的做画纸画一张比较细致的设计稿（做画=作画）",
            "这张图是我打印的千语千询的其中一张Lightout（Lightout=layout、千语千询=千与千寻）"]
        q["reference_answer"] = ("视频中 layout（转写为 Lightout）位于分镜之后：画面细节不准时，需要用标准作画纸画一张细致的设计稿；"
                                 "layout 可单独指设计稿这一张画，也可指 layout 加整个一原（v0006）。")
        q["evaluation_notes"] = "whisper 同音变体：Lightout/Lineout=layout、一元=一原。评分接受变体。"
    out.append(q)

with open("data/eval/dev_questions.jsonl", "w", encoding="utf-8") as f:
    for q in out:
        f.write(json.dumps(q, ensure_ascii=False) + "\n")
print("ok")

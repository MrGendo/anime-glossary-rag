# -*- coding: utf-8 -*-
"""Append refusal + out-of-scope + video questions to dev set (target 30).
Every answerable=false question gets refusal criteria in required_facts."""
import json, re

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
by_term = {}
for c in chunks:
    if c["chunk_id"].startswith("g"):
        by_term.setdefault(c["section_title"], c)
vid = {c["chunk_id"]: c for c in chunks if c["chunk_id"].startswith("v")}

qs = [json.loads(l) for l in open("data/eval/dev_questions.jsonl", encoding="utf-8")]

def q(qid, question, qtype, diff, ref, facts, evs, srcs, pages, answerable, notes=""):
    return {"question_id": qid, "question": question, "question_type": qtype,
            "difficulty": diff, "reference_answer": ref, "required_facts": facts,
            "evidence_chunk_ids": evs, "source_ids": srcs, "page_numbers": pages,
            "answerable": answerable, "acceptable_variants": [], "evaluation_notes": notes}

# --- video-sourced process questions (answerable) ---
qs.append(q("PV-001", "按视频讲解，日式动画画面制作的流程顺序是什么？（中文口径）",
    "process_flow", 2,
    "脚本→分镜→layout→原画→中割→上色→摄影→剪辑（视频明确跳过前期设定企划与声音环节，只讲实际画面制作）。",
    ["前期、中期、后期及音乐音效四部分（画面制作为主）",
     "脚本/分镜/layout/原画/中割/上色/摄影/剪辑 顺序"],
    ["v0002", "v0003", "v0004"], ["video/BV1vRjZzUEwN"], None, True,
    notes="视频块 v0002-v0004；评分按流程顺序要素计分。"))
qs.append(q("PV-002", "视频中 layout（布局）环节的产出是什么？它在流程中的位置？",
    "term_def", 2,
    "layout 位于分镜（コンテ）之后、原画之前，是根据分镜设计每卡画面（人物位置、空间关系、镜头运动轨迹）的环节，产出是 layout 稿，供原画和背景参考。",
    ["layout 根据分镜绘制", "产出供原画/背景使用的画面设计稿"],
    ["v0003", "v0004"], ["video/BV1vRjZzUEwN"], None, True,
    notes="中文口径与书中レイアウト互补。"))

# --- insufficient evidence (should refuse) ---
qs.append(q("RF-001", "《SHIROBAKO》第3话的具体原画师是谁？",
    "insufficient", 1,
    "知识库无此信息，应拒答（库内无具体作品人员表）。",
    ["库内无具体作品的制作人员信息"], [], [], None, False,
    notes="SHIROBAKO 仅作为 BGM 出处出现在视频简介，非知识点。"))
qs.append(q("RF-002", "2000年代日本动画原画师的平均工资是多少？",
    "insufficient", 1,
    "知识库无薪资数据，应拒答。",
    ["库内无薪资/收入信息"], [], [], None, False))
qs.append(q("RF-003", "京都动画公司的動画部门有多少人？",
    "insufficient", 1,
    "知识库无具体公司组织规模数据，应拒答。",
    ["库内无公司组织规模数据"], [], [], None, False))
qs.append(q("RF-004", "神村幸子本人担任过哪些作品的作画監督？",
    "insufficient", 2,
    "知识库（本书 OCR）无作者履历信息，应拒答。",
    ["库内无作者个人履历"], [], [], None, False))

# --- out of scope (should refuse) ---
qs.append(q("OS-001", "迪士尼动画的全动画制作流程是怎样的？",
    "out_of_scope", 1,
    "超出知识库边界（日式有限动画术语/分工），应拒答或声明库外。",
    ["库内仅有リミテッドアニメーション词条提及美国背景，无迪士尼流程"], [], [], None, False))
qs.append(q("OS-002", "3DCG 建模的拓扑布线规范有哪些？",
    "out_of_scope", 1,
    "超出知识库边界，应拒答（库内 3DCG 词条仅术语级定义）。",
    ["库内无 3D 建模技术细节"], [], [], None, False))
qs.append(q("OS-003", "动画声优的试音流程是怎样的？",
    "out_of_scope", 1,
    "超出知识库边界（声音环节明确排除），应拒答。",
    ["库内声优/キャスティング仅词条级，无试音流程"], [], [], None, False))
qs.append(q("OS-004", "日本动画 Blu-ray 的定价策略是什么？",
    "out_of_scope", 1,
    "超出知识库边界（商业模式排除），应拒答。",
    ["库内无商业/定价信息"], [], [], None, False))

with open("data/eval/dev_questions.jsonl", "w", encoding="utf-8") as f:
    for s in qs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

from collections import Counter
print("total:", len(qs))
print(Counter(s["question_type"] for s in qs))
print("answerable:", sum(1 for s in qs if s["answerable"]))
# sanity: evidence chunk ids exist
all_ids = {c["chunk_id"] for c in chunks}
bad = [cid for s in qs for cid in s["evidence_chunk_ids"] if cid not in all_ids]
print("bad evidence ids:", bad)

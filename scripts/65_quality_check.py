# -*- coding: utf-8 -*-
"""Data quality checker: independent program auditing chunks.jsonl.
Checks: empty/too-short, duplicates, missing metadata, missing page/ts,
suspicious OCR chars, term anomalies, eval-answer supportability.
Outputs data/quality/quality_report.json + manual review list."""
import json, os, re, unicodedata
from collections import Counter

os.makedirs("data/quality", exist_ok=True)
chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]

issues = {"empty_text": [], "short_text": [], "dup_text": [],
          "missing_page_book": [], "missing_ts_video": [], "missing_meta": [],
          "suspicious_chars": [], "headword_fixed": [], "near_empty_body": []}

# 1. empty / short
for c in chunks:
    t = c["text"].strip()
    if not t:
        issues["empty_text"].append(c["chunk_id"])
    elif len(t) < 15:
        issues["short_text"].append((c["chunk_id"], t[:30]))

# 2. duplicates (exact squashed text)
seen = {}
for c in chunks:
    key = re.sub(r"\s+", "", c["text"])[:200]
    if key in seen:
        issues["dup_text"].append((seen[key], c["chunk_id"]))
    else:
        seen[key] = c["chunk_id"]

# 3/4. metadata
REQ = ["chunk_id", "text", "source_id", "source_title", "source_type",
       "page_number", "timestamp", "section_title", "language",
       "extraction_method", "verification_status"]
for c in chunks:
    for f in REQ:
        if f not in c:
            issues["missing_meta"].append((c["chunk_id"], f))
    if c["source_type"] == "book" and c["page_number"] is None:
        issues["missing_page_book"].append(c["chunk_id"])
    if c["source_type"] == "video" and not c["timestamp"]:
        issues["missing_ts_video"].append(c["chunk_id"])

# 5. suspicious OCR chars in glossary chunks (rare CJK blocks, replacement, etc.)
SUSP = re.compile(r"[ＯＸ□■〇◆◇※→⇒]+")
def rare_ratio(t):
    if not t: return 0
    n = 0
    for ch in t:
        if ch.isalpha() or ch.isspace():
            continue
        try:
            name = unicodedata.name(ch)
        except ValueError:
            n += 1; continue
        if "CJK" not in name and ch not in "（）「」・。、：；":
            n += 1
    return n / len(t)
for c in chunks:
    if c["chunk_id"].startswith("g"):
        if rare_ratio(c["text"]) > 0.25:
            issues["suspicious_chars"].append((c["chunk_id"], c["text"][:24]))
        if c["verification_status"] == "headword_fixed_by_reading":
            issues["headword_fixed"].append(
                (c["chunk_id"], c["extra"].get("term_raw"), c["section_title"]))
        body = c["text"].split(":", 1)[-1].strip()
        if len(body) < 8:
            issues["near_empty_body"].append((c["chunk_id"], c["section_title"]))

# 6. eval answer supportability: every answerable question's facts anchored
squash = lambda s: re.sub(r"\s+", "", s)
by_cid = {c["chunk_id"]: c["text"] for c in chunks}
unsup = []
for split in ("dev", "final"):
    path = f"data/eval/{split}_questions.jsonl"
    for l in open(path, encoding="utf-8"):
        q = json.loads(l)
        if not q["answerable"]:
            continue
        if not q["evidence_chunk_ids"]:
            unsup.append((split, q["question_id"], "no evidence"))
            continue
        ev = squash(" ".join(by_cid.get(c, "") for c in q["evidence_chunk_ids"]))
        for fact in q["required_facts"]:
            runs = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{6,}", fact)
            if runs and not any(squash(r) in ev for r in runs):
                unsup.append((split, q["question_id"], runs[0][:20]))

# glossary order violations count (from earlier strong check)
viol = sum(1 for _ in open("data/processed/glossary_order_violations.jsonl", encoding="utf-8"))

report = {
    "total_chunks": len(chunks),
    "glossary": sum(1 for c in chunks if c["chunk_id"].startswith("g")),
    "video": sum(1 for c in chunks if c["chunk_id"].startswith("v")),
    "chapter": sum(1 for c in chunks if c["chunk_id"].startswith("c")),
    "empty_text": len(issues["empty_text"]),
    "short_text": len(issues["short_text"]),
    "dup_text_pairs": len(issues["dup_text"]),
    "missing_meta": len(issues["missing_meta"]),
    "missing_page_book": len(issues["missing_page_book"]),
    "missing_ts_video": len(issues["missing_ts_video"]),
    "suspicious_chars_glossary": len(issues["suspicious_chars"]),
    "headword_fixed_by_reading": len(issues["headword_fixed"]),
    "near_empty_body": len(issues["near_empty_body"]),
    "eval_unsupported_facts": len(unsup),
    "glossary_order_violations": viol,
    "detail": {k: (v[:12] if isinstance(v, list) else v) for k, v in issues.items()},
    "eval_unsupported_detail": unsup[:10],
}
json.dump(report, open("data/quality/quality_report.json", "w"), ensure_ascii=False, indent=1)

# manual review list
with open("data/quality/manual_review_list.md", "w", encoding="utf-8") as f:
    f.write("# 人工抽检清单（自动检查产出，待人工核验）\n\n")
    f.write("## 1. 词头OCR误读已按注音修复（需对照原页图核验）\n")
    for cid, raw, canon in issues["headword_fixed"]:
        f.write(f"- {cid}: {raw} → {canon}\n")
    f.write("\n## 2. 释义体近空（可能跨页丢失）\n")
    for cid, t in issues["near_empty_body"]:
        f.write(f"- {cid}: {t}\n")
    f.write("\n## 3. 可疑字符比例高的词条\n")
    for cid, t in issues["suspicious_chars"]:
        f.write(f"- {cid}: {t}...\n")
    f.write(f"\n## 4. 五十音序违例对（共{viol}对，见 glossary_order_violations.jsonl）\n")
    f.write("- 前三对示例见 data/processed/glossary_order_violations.jsonl\n")

for k, v in report.items():
    if k not in ("detail", "eval_unsupported_detail"):
        print(f"{k}: {v}")

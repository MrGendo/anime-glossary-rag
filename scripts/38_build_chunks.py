# -*- coding: utf-8 -*-
"""Build the unified chunks.jsonl (glossary entries + chapter text + video).

Sources:
- data/processed/glossary_full.jsonl (549 entries, headwords incl. OCR misreads)
- data/processed/video_chunks_raw.jsonl (12 video chunks)
- chapters 1/3/5 reconstructed inline from ocr_boxes.jsonl (ch2 manga bubbles skipped)

Applies term normalization (reading-based map from scripts/36) so misread
headwords get their canonical name, flagged verification_status.
"""
import json, os, re

os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/indexes", exist_ok=True)

# ---------------------------------------------------------------- normalization
NORM_BY_READING = {
    "げんが": "原画", "にげん": "二原", "さくがかんとく": "作画監督", "さくが": "作画",
    "どうが": "動画", "あたり": "アタリ", "しあげけんさ": "仕上検査",
    "どうがけんさ": "動画検査",
}
NORM_BY_TERM = {"原面": "原画", "二豚": "二原", "作画監替": "作画監督", "作雨": "作画",
                "仕上検": "仕上検査"}

entries = [json.loads(l) for l in open("data/processed/glossary_full.jsonl", encoding="utf-8")]

chunks = []
n_misread = 0
for i, e in enumerate(entries, 1):
    term = e["term"].strip()
    reading = e["reading"].strip()
    canonical = NORM_BY_TERM.get(term) or NORM_BY_READING.get(
        re.sub(r"[^ぁ-んー]", "", reading))
    status = "auto_ok"
    term_disp = term
    if canonical and canonical != term:
        term_disp = canonical
        status = "headword_fixed_by_reading"
        n_misread += 1
    text = f"{term_disp}（{reading}）: {e['body']}" if e["body"].strip() else f"{term_disp}（{reading}）"
    chunks.append({
        "chunk_id": f"g{i:04d}",
        "text": text,
        "source_id": "pdf/anime_daihyakka",
        "source_title": "アニメーションの基礎知識大百科（神村幸子）",
        "source_type": "book",
        "page_number": e["page"],
        "timestamp": None,
        "section_title": term_disp,
        "language": "ja",
        "extraction_method": "vision_ocr",
        "verification_status": status,
        "extra": {"term_raw": term, "reading": reading, "col": e.get("col")},
    })

# ---------------------------------------------------------------- video chunks
for v in (json.loads(l) for l in open("data/processed/video_chunks_raw.jsonl", encoding="utf-8")):
    chunks.append({
        "chunk_id": v["chunk_id"],
        "text": v["text"],
        "source_id": "video/BV1vRjZzUEwN",
        "source_title": "【从零学动画01】日式动画全流程（阿咪画不完）",
        "source_type": "video",
        "page_number": None,
        "timestamp": v["timestamp"],
        "section_title": f"video {v['timestamp']}",
        "language": "zh",
        "extraction_method": "whisper_cpp_small",
        "verification_status": "auto_ok",
        "extra": {"start": v["start"], "end": v["end"]},
    })

# ---------------------------------------------------------------- chapters 1/3/5
pages = {}
for line in open("data/raw/ocr_boxes.jsonl", encoding="utf-8"):
    d = json.loads(line)
    pno = int(re.search(r"p(\d+)", d["image"]).group(1))
    pages[pno] = d["boxes"]

CH = {1: (9, 20, "第1章 アニメーションはこうしてできる"),
      3: (43, 64, "第3章 制作進行ドキュメント"),
      5: (209, 224, "第5章 付録")}

def col_lines(boxes, ncols=1):
    """Chapters 1/3 are mostly label+body single flow; use 1 column but sort
    by y then x; drop running header (y>0.93) and page numbers."""
    bs = [b for b in boxes if b["y"] < 0.93]
    bs.sort(key=lambda b: (-b["y"], b["x"]))
    lines, cur = [], None
    for b in bs:
        if cur and abs(cur["y"] - b["y"]) < min(cur["h"], b["h"]) * 0.5:
            cur["text"] += b["text"]
        else:
            if cur: lines.append(cur)
            cur = dict(b)
    if cur: lines.append(cur)
    return lines

NOISE = re.compile(r"^[\s0-9０-９①-⑳•●・\-—.。]{1,4}$")
n_ch = 0
for ch, (p0, p1, title) in CH.items():
    buf, p_start = [], None
    for pno in range(p0, p1 + 1):
        for ln in col_lines(pages.get(pno, [])):
            t = ln["text"].strip()
            if not t or NOISE.match(t) or len(t) <= 1:
                continue
            if t.startswith("第") and "章" in t[:6]:
                continue  # running header remainder
            buf.append((pno, t))
    # aggregate into <=500-char chunks, breaking preferentially at ●/numbered items
    cur_texts, cur_page = [], None
    def flush():
        global n_ch
        if not cur_texts:
            return
        n_ch += 1
        chunks.append({
            "chunk_id": f"c{n_ch:04d}",
            "text": "\n".join(cur_texts),
            "source_id": "pdf/anime_daihyakka",
            "source_title": "アニメーションの基礎知識大百科（神村幸子）",
            "source_type": "book",
            "page_number": cur_page,
            "timestamp": None,
            "section_title": title,
            "language": "ja",
            "extraction_method": "vision_ocr",
            "verification_status": "auto_ok",
            "extra": {"chapter": ch},
        })
    size = 0
    for pno, t in buf:
        if cur_page is None:
            cur_page = pno
        if size + len(t) > 500 and cur_texts:
            flush_old = cur_texts, cur_page
            # python closure workaround: manual
            n_ch += 1
            chunks.append({
                "chunk_id": f"c{n_ch:04d}",
                "text": "\n".join(cur_texts),
                "source_id": "pdf/anime_daihyakka",
                "source_title": "アニメーションの基礎知識大百科（神村幸子）",
                "source_type": "book",
                "page_number": cur_page,
                "timestamp": None,
                "section_title": title,
                "language": "ja",
                "extraction_method": "vision_ocr",
                "verification_status": "auto_ok",
                "extra": {"chapter": ch},
            })
            cur_texts, cur_page, size = [], None, 0
            continue
        cur_texts.append(t)
        size += len(t)
    if cur_texts:
        n_ch += 1
        chunks.append({
            "chunk_id": f"c{n_ch:04d}",
            "text": "\n".join(cur_texts),
            "source_id": "pdf/anime_daihyakka",
            "source_title": "アニメーションの基礎知識大百科（神村幸子）",
            "source_type": "book",
            "page_number": cur_page,
            "timestamp": None,
            "section_title": title,
            "language": "ja",
            "extraction_method": "vision_ocr",
            "verification_status": "auto_ok",
            "extra": {"chapter": ch},
        })

with open("data/processed/chunks.jsonl", "w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

g = sum(1 for c in chunks if c["chunk_id"].startswith("g"))
v = sum(1 for c in chunks if c["chunk_id"].startswith("v"))
cc = sum(1 for c in chunks if c["chunk_id"].startswith("c"))
empty = sum(1 for c in chunks if not c["text"].strip())
ids = [c["chunk_id"] for c in chunks]
print(f"total chunks: {len(chunks)} | glossary {g} (misread-fixed {n_misread}) | video {v} | chapter {cc}")
print(f"empty text: {empty} | unique ids: {len(set(ids))}")
no_page = [c["chunk_id"] for c in chunks if c["source_type"] == "book" and c["page_number"] is None]
print(f"book chunks without page: {len(no_page)}")

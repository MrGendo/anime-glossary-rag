# -*- coding: utf-8 -*-
"""Convert whisper transcript to video chunks with timestamps.
Merge whisper segments into topical chunks (~<=400 chars), keep timestamps."""
import json

d = json.load(open("data/raw/bili_transcript.json", encoding="utf-8"))
segs = d["transcription"]

chunks = []
cur_texts, cur_start = [], None
MAXC = 380
for s in segs:
    t = s["text"].strip()
    if not t:
        continue
    ts = round(s["offsets"]["from"] / 1000, 1)
    if cur_start is None:
        cur_start = ts
    cur_texts.append(t)
    if sum(len(x) for x in cur_texts) >= MAXC:
        chunks.append((cur_start, ts + round((s["offsets"]["to"] - s["offsets"]["from"]) / 1000, 1), " ".join(cur_texts)))
        cur_texts, cur_start = [], None
if cur_texts:
    chunks.append((cur_start, round(segs[-1]["offsets"]["to"] / 1000, 1), " ".join(cur_texts)))

out = open("data/processed/video_chunks_raw.jsonl", "w", encoding="utf-8")
for i, (st, ed, txt) in enumerate(chunks, 1):
    out.write(json.dumps({
        "chunk_id": f"v{i:04d}",
        "text": txt,
        "timestamp": f"{int(st//60):02d}:{int(st%60):02d}-{int(ed//60):02d}:{int(ed%60):02d}",
        "start": st, "end": ed,
        "language": "zh",
        "extraction_method": "whisper_cpp_small",
    }, ensure_ascii=False) + "\n")
print("video chunks:", len(chunks))
for c in chunks[:3]:
    print(c[0], c[2][:60])

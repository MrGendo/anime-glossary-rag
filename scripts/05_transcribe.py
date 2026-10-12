# -*- coding: utf-8 -*-
"""Transcribe bilibili audio with faster-whisper (zh). Output: data/raw/video_transcript.jsonl"""
import json
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    "data/raw/bili_audio.wav",
    language="zh",
    vad_filter=True,
    beam_size=5,
)
out = open("data/raw/video_transcript.jsonl", "w", encoding="utf-8")
for seg in segments:
    rec = {"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()}
    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[{seg.start:7.2f} -> {seg.end:7.2f}] {seg.text.strip()[:80]}")
out.close()
print("saved data/raw/video_transcript.jsonl | lang prob:", info.language_probability)

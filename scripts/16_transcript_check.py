# -*- coding: utf-8 -*-
"""Inspect whisper transcript quality."""
import json

d = json.load(open("data/raw/bili_transcript.json", encoding="utf-8"))
segs = d["transcription"]
print("segments:", len(segs))
total_dur = 0
for s in segs:
    total_dur += s["offsets"]["to"] - s["offsets"]["from"]
print("covered duration: %.1fs / 968s" % (total_dur / 1000))

for s in segs[:18]:
    t = s["offsets"]["from"] / 1000
    print(f"[{int(t//60):02d}:{int(t%60):02d}] {s['text']}")
print("...")
for s in segs[-6:]:
    t = s["offsets"]["from"] / 1000
    print(f"[{int(t//60):02d}:{int(t%60):02d}] {s['text']}")

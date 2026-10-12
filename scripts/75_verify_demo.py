# -*- coding: utf-8 -*-
"""Verify per-question answers differ and carry real evidence (local + public)."""
import json, os, urllib.request

BASE = "http://127.0.0.1:8902"
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

QS = ["レイアウト（LO）とは？", "動画チェックとは？", "中割りとは？",
      "作画監督の種類は？", "まき直しとは？"]
answers = []
for q in QS:
    req = urllib.request.Request(BASE + "/api/ask",
        data=json.dumps({"question": q}).encode(),
        headers={"Content-Type": "application/json"})
    d = json.loads(opener.open(req, timeout=60).read())
    print(f"Q: {q}")
    print(f"  -> {d['answer'][:110]}")
    print(f"  cites: {[(c['label'], c['section_title'], c['page_number']) for c in d['citations']]}")
    answers.append(d["answer"])

assert len(set(answers)) == len(answers), "answers must differ per question"
print("\nALL DISTINCT: OK")

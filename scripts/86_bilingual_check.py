# -*- coding: utf-8 -*-
"""Bilingual answer verification (3 questions + 1 refusal)."""
import json, os, urllib.request

BASE = "http://127.0.0.1:8902"
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def ask(q):
    req = urllib.request.Request(BASE + "/api/ask",
        data=json.dumps({"question": q}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(opener.open(req, timeout=120).read())

for q in ["原画和動画（中割り）的职责有什么区别？",
          "動画チェック是检查什么的？",
          "レイアウト用紙とは何ですか？（日本語のみで答えてください）",
          "Netflix 对日本动画外包的采购价怎么谈？"]:
    d = ask(q)
    has_zh = "【中文】" in d["answer"]
    print(f"Q: {q[:40]}")
    print(f"  refusal={d['refusal']} bilingual={has_zh}")
    print("  ", d["answer"][:150].replace("\n", " ⏎ "))
    print("  cites:", [c["section_title"] for c in d["citations"]][:3])
    print()

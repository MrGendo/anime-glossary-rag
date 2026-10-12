# -*- coding: utf-8 -*-
"""Real-LLM end-to-end check: answer quality, citations, refusal path."""
import json, os, urllib.request

BASE = "http://127.0.0.1:8902"
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def ask(q):
    req = urllib.request.Request(BASE + "/api/ask",
        data=json.dumps({"question": q}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(opener.open(req, timeout=120).read())

# 1. in-scope question
d = ask("レイアウト（LO）とは何ですか？絵コンテとの違いも教えてください")
print("== RAG answer ==")
print(d["answer"][:400])
print("citations:", [(c["label"], c["section_title"], c["page_number"]) for c in d["citations"]])
print("model:", d["model"], "| latency:", d["latency_ms"], "ms")

# 2. out-of-scope question (must refuse)
d2 = ask("Netflix 对日本动画外包的采购价怎么谈？")
print("\n== out-of-scope ==")
print("refusal:", d2["refusal"])
print(d2["answer"][:200])

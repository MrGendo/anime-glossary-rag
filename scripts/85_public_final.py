# -*- coding: utf-8 -*-
"""Public smoke test in real-LLM mode (topic labeling + answer quality)."""
import json, os, urllib.request

BASE = "https://pac-estimation-oil-health.trycloudflare.com"
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

h = json.loads(opener.open(BASE + "/api/health", timeout=30).read())
print("health:", h)
req = urllib.request.Request(BASE + "/api/ask",
    data=json.dumps({"question": "原画和動画（中割り）的职责有什么区别？"}).encode(),
    headers={"Content-Type": "application/json"})
d = json.loads(opener.open(req, timeout=120).read())
print("llm:", d["model"], "| latency:", d["latency_ms"], "ms")
print("answer:", d["answer"][:280])
print("citations:", [(c["label"], c["section_title"], c["page_number"]) for c in d["citations"]])
html = opener.open(BASE + "/", timeout=30).read().decode()
print("topic labeled in frontend:", "小 topic" in html)

# -*- coding: utf-8 -*-
"""Real public-internet verification of the deployed tunnel."""
import json
import os
import urllib.request

BASE = "https://pac-estimation-oil-health.trycloudflare.com"
# bypass local proxy for direct public test
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

r = opener.open(BASE + "/api/health", timeout=30)
health = json.loads(r.read())
print("HEALTH:", health)
assert health["status"] == "ok"

req = urllib.request.Request(
    BASE + "/api/ask",
    data=json.dumps({"question": "レイアウト（LO）とは何ですか？"}).encode(),
    headers={"Content-Type": "application/json"})
r2 = opener.open(req, timeout=60)
d = json.loads(r2.read())
print("ASK ok:", d["ok"], "| req:", d["request_id"], "| hits:", len(d["retrieval"]))
print("top hit:", d["retrieval"][0]["chunk_id"], d["retrieval"][0]["section_title"],
      "p", d["retrieval"][0]["page_number"], "score", round(d["retrieval"][0]["score"], 2))
print("answer (mock):", (d["answer"] or "")[:120])

r3 = opener.open(BASE + "/", timeout=30)
html = r3.read().decode()
print("frontend served:", "动画术语知识库" in html, "| key leaked:", "ZHIPU_API_KEY" in html)

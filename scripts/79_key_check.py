# -*- coding: utf-8 -*-
"""Verify the provided ZHIPU key works (glm-4-flash) with one tiny call."""
import json, os, sys, urllib.request

key = [l.strip().split("=", 1)[1] for l in open(".env") if l.startswith("ZHIPU_API_KEY=")][0]
body = json.dumps({
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "回复两个字：正常"}],
    "max_tokens": 16,
}).encode()
req = urllib.request.Request(
    "https://open.bigmodel.cn/api/paas/v4/chat/completions", data=body,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    print("OK:", d["choices"][0]["message"]["content"], "| usage:", d.get("usage"))
except Exception as e:
    print("FAILED:", type(e).__name__, str(e)[:200])
    sys.exit(1)

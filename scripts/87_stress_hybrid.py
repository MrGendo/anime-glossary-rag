# -*- coding: utf-8 -*-
"""Stability stress: 8 consecutive real-LLM hybrid queries (the crash trigger
was previously the FIRST concurrent request after vector load)."""
import json, os, time, urllib.request

BASE = "http://127.0.0.1:8902"
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

QS = ["レイアウトとは？", "動画検査は何をチェックする？", "中割りとは？",
      "作画監督の種類は？", "まき直しとは？", "タイムシートとは？",
      "色指定と色彩設定の違いは？", "カット袋に何を書く？"]
ok = 0
for i, q in enumerate(QS, 1):
    try:
        req = urllib.request.Request(BASE + "/api/ask",
            data=json.dumps({"question": q}).encode(),
            headers={"Content-Type": "application/json"})
        d = json.loads(opener.open(req, timeout=120).read())
        ok += d.get("ok", False)
        print(f"{i}. {q[:24]:26s} ok={d.get('ok')} hits={len(d.get('retrieval', []))} "
              f"bilingual={'【中文】' in (d.get('answer') or '')} {d.get('latency_ms')}ms")
    except Exception as e:
        print(f"{i}. {q[:24]:26s} FAILED {type(e).__name__} {str(e)[:80]}")
    time.sleep(1)
print(f"\n{ok}/{len(QS)} succeeded")
h = json.loads(opener.open(BASE + "/api/health", timeout=15).read())
print("service alive after stress:", h["status"])

# -*- coding: utf-8 -*-
"""Vision-LLM spot check of OCR pages via zhipu glm-4.5v.
Reads key from studio .env (LLM_API_KEY). Verifies glossary pages & empty-body entries."""
import base64, json, os, sys, urllib.request

ENV = "/Users/Admin/Downloads/project/LALIDA_AI_资产件夹/11_STUDIO_短剧工作台/server/.env"
key = None
for ln in open(ENV, encoding="utf-8"):
    if ln.startswith("LLM_API_KEY="):
        key = ln.strip().split("=", 1)[1]
if not key:
    sys.exit("no key")

def ask(img_path, question, retries=4):
    import time
    b64 = base64.b64encode(open(img_path, "rb").read()).decode()
    body = json.dumps({
        "model": "glm-4.5v",
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": question},
        ]}],
        "max_tokens": 4096,
        "temperature": 0.1,
    }).encode()
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(retries):
        req = urllib.request.Request(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            if "choices" not in d:
                return json.dumps(d, ensure_ascii=False)[:300]
            return d["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(15 * (attempt + 1))
                continue
            raise

if __name__ == "__main__":
    pages = sys.argv[1:] or ["101", "115", "164"]
    for p in pages:
        out = ask(f"data/raw/pages_all/p{int(p):03d}.png",
                  "请逐条抄录本页左栏和右栏中所有「词条名（注音）」格式的词条头，按栏内出现顺序输出，"
                  "每行一个，格式：[栏0|栏1] 词条名。不要解释。")
        print(f"===== p{p} =====")
        print(out[:1500])
        print()

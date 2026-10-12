"""Scan glossary for target terms + check pytest + violations format."""
import json
import subprocess

# 1. violations file format
with open('data/processed/glossary_order_violations.jsonl') as f:
    v = [json.loads(l) for l in f]
print("violations:", len(v), "keys:", sorted(v[0].keys()) if v else None)
print("first:", json.dumps(v[0], ensure_ascii=False)[:200] if v else None)

# 2. find target terms -> entry ids (1-based line number == g-index)
targets = ['レイアウト', ' Layout', 'Layout', '原画', '動画', '中割', '動画チェック',
           '作画監督', '原画マン', '動画マン', '制作進行', '絵コンテ', '演出', '撮影',
           '背景', '美術', '仕上げ']
with open('data/processed/glossary_full.jsonl') as f:
    entries = [json.loads(l) for l in f]
print("\ntotal entries:", len(entries))
for i, e in enumerate(entries, 1):
    t = e['term']
    if any(k in t for k in ['レイアウト', 'LAYOUT', 'LAYOUTS', 'ラフ', '原画', '動画', '中割',
                            '作画', '制作進行', 'コンテ', '演出', '撮影', '背景', '美術',
                            '仕上げ', 'キャラクター設定', 'キャラクターデザイン', 'ラyout']):
        print(f"  g{i:04d} p{e['page']} c{e['col']} | {t} | {e['reading'][:20]}")

# 3. pytest present?
r = subprocess.run(['.venv/bin/python', '-m', 'pytest', '--version'], capture_output=True, text=True)
print("\npytest:", r.stdout.strip() or r.stderr.strip())

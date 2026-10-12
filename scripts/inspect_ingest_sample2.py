"""Deeper look: full boxes on more sample pages."""
import json

rows = [json.loads(l) for l in open('data/raw/ocr_boxes.jsonl')]

for p in [11, 12, 23, 24, 45, 46, 211, 212, 223, 224]:
    r = rows[p - 1]
    bs = r['boxes']
    print(f"\n=== p{p} boxes={len(bs)}")
    for b in sorted(bs, key=lambda b: -b['y']):
        t = b['text'][:52]
        print(f"  y={b['y']:.3f} x={b['x']:.3f} w={b['w']:.3f} h={b['h']:.3f} | {t}")

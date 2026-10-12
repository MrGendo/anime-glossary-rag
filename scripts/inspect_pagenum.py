"""Find page-number boxes and header-band boxes (fixed page parse)."""
import json
import re

rows = [json.loads(l) for l in open('data/raw/ocr_boxes.jsonl')]


def page_no(image):
    m = re.search(r'p(\d+)\.png$', image)
    return int(m.group(1)) if m else None


print("--- small digit-only boxes (candidate page numbers) ---")
for r in rows:
    page = page_no(r['image'])
    for b in r['boxes']:
        t = b['text'].strip()
        if t.isdigit() and len(t) <= 3:
            print(f"  p{page} y={b['y']:.3f} x={b['x']:.3f} h={b['h']:.3f} | {t}")

print("\n--- boxes with y>0.93 (header band), unique text prefixes ---")
seen = set()
for r in rows:
    page = page_no(r['image'])
    for b in r['boxes']:
        if b['y'] > 0.93:
            t = b['text'][:44]
            key = t[:12]
            if key not in seen:
                seen.add(key)
                print(f"  p{page} y={b['y']:.3f} x={b['x']:.3f} | {t}")

print("\n--- boxes with y<0.06 (bottom band), unique text prefixes ---")
seen = set()
for r in rows:
    page = page_no(r['image'])
    for b in r['boxes']:
        if b['y'] < 0.06:
            t = b['text'][:44]
            key = t[:12]
            if key not in seen:
                seen.add(key)
                print(f"  p{page} y={b['y']:.3f} x={b['x']:.3f} | {t}")

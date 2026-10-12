"""Quick look at OCR boxes on sample pages (read-only)."""
import json

rows = [json.loads(l) for l in open('data/raw/ocr_boxes.jsonl')]
print("pages:", len(rows))

for p in [9, 10, 21, 22, 43, 44, 209, 210]:
    r = rows[p - 1]
    bs = r['boxes']
    print(f"\n=== p{p} image={r['image']} boxes={len(bs)}")
    for b in sorted(bs, key=lambda b: -b['y'])[:14]:
        t = b['text'][:38]
        print(f"  y={b['y']:.3f} x={b['x']:.3f} w={b['w']:.3f} h={b['h']:.3f} | {t}")

# -*- coding: utf-8 -*-
"""Find アタリ entry: p90 dump earlier showed 'アタリ／あたり（あたり）' on p90.
Check glossary_full for page 90 terms."""
import json

entries = [json.loads(l) for l in open("data/processed/glossary_full.jsonl", encoding="utf-8")]
for e in entries:
    if e["page"] == 90:
        print(f"p90 {e['term']}（{e['reading']}） | {e['body'][:80]}")

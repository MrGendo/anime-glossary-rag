# -*- coding: utf-8 -*-
"""Directly construct VectorRetriever over real chunks, no eval runner.
Env pinned single-thread to dodge the loky/OMP segfault."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, sys, time
sys.path.insert(0, ".")

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
print("chunks:", len(chunks), flush=True)

from app.retrieval.vector import VectorRetriever
t0 = time.time()
vr = VectorRetriever(chunks)
print(f"built in {time.time()-t0:.1f}s", flush=True)
hits = vr.search("レイアウトとは？", top_k=3)
for h in hits:
    print(h.chunk_id, round(h.score, 3), h.section_title)
vr.save("data/indexes/vector")
print("saved", flush=True)

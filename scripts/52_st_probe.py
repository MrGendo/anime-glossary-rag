# -*- coding: utf-8 -*-
"""Try single-process encode to isolate the segfault (loky/faiss conflict?)."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
sys.path.insert(0, ".")

print("importing ST...", flush=True)
from sentence_transformers import SentenceTransformer
print("loading model...", flush=True)
m = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
print("encoding 2...", flush=True)
v = m.encode(["レイアウトとは", "原画の仕事"], normalize_embeddings=True)
print("encode ok", v.shape, flush=True)
print("encoding 700...", flush=True)
v2 = m.encode(["レイアウトとは"] * 700, normalize_embeddings=True, batch_size=64)
print("bulk ok", v2.shape, flush=True)
import faiss  # now load faiss AFTER st used
import numpy as np
idx = faiss.IndexFlatIP(v.shape[1])
idx.add(np.ascontiguousarray(v2.astype("float32")))
print("faiss add ok", idx.ntotal, flush=True)
D, I = idx.search(v.astype("float32"), 3)
print("faiss search ok", I[0], flush=True)

import sys
sys.path.insert(0, ".")
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.tokenizer import tokenize
from tests.test_retrieval import CHUNKS

r = BM25Retriever(CHUNKS)
ids = [str(c["chunk_id"]) for c in CHUNKS]
for q in ["作画監督", "アフレコ"]:
    print("Q:", q, "tokens:", tokenize(q))
    for h in r.search(q, top_k=4):
        idx = ids.index(h.chunk_id)
        print(f"  {h.chunk_id} {h.score:.3f} tokens={len(r._tokenized_corpus[idx])} :: {h.text_snippet[:40]}")

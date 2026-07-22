"""RAG vector store over the knowledge-base chunks.

Embedded, self-contained, zero-server (works on this Python 3.14 setup):
  - with OPENAI_API_KEY  → OpenAI `text-embedding-3-small` + cosine similarity
  - without a key        → offline BM25-style lexical retrieval (deterministic)
Metadata filters (part_no, doc_type, op_no) let agents scope retrieval.
Production swap: the same interface backs onto Chroma / Qdrant unchanged.
"""
import math
import os
import re
from collections import Counter

import numpy as np

EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
_TOKEN = re.compile(r"[a-z0-9]+")


def _tok(text):
    return _TOKEN.findall((text or "").lower())


class VectorStore:
    def __init__(self):
        self.chunks = []
        self.mode = "lexical"
        self._emb = None          # np.ndarray [n, d] when vector mode
        self._df = Counter()      # document frequencies for lexical mode
        self._toks = []           # tokenised chunks for lexical mode
        self._avg_len = 1.0

    # ---- build -------------------------------------------------------------
    def build(self, chunks):
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        if not texts:                      # empty knowledge base (clean start)
            self.mode = "empty"
            self._toks = []
            return self
        if os.environ.get("OPENAI_API_KEY"):
            try:
                self._emb = self._embed_cached(texts)
                self.mode = "openai"
                return self
            except Exception as e:  # noqa: BLE001
                print("[rag] embedding failed, falling back to lexical:", e)
        # lexical fallback
        self.mode = "lexical"
        self._toks = [_tok(t) for t in texts]
        self._avg_len = (sum(len(t) for t in self._toks) / len(self._toks)) if self._toks else 1.0
        for toks in self._toks:
            for term in set(toks):
                self._df[term] += 1
        return self

    def _embed_cached(self, texts):
        """Cache embeddings on disk keyed by content hash — avoids re-paying on restart."""
        import hashlib
        key = hashlib.md5(("|".join(texts) + EMBED_MODEL).encode("utf-8")).hexdigest()[:16]
        os.makedirs("outputs/emb_cache", exist_ok=True)
        path = os.path.join("outputs/emb_cache", f"{key}.npy")
        if os.path.exists(path):
            return np.load(path)
        arr = self._embed(texts)
        np.save(path, arr)
        return arr

    def _embed(self, texts):
        from openai import OpenAI
        client = OpenAI()
        vecs = []
        for i in range(0, len(texts), 128):
            batch = texts[i:i + 128]
            resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
            vecs.extend([d.embedding for d in resp.data])
        arr = np.array(vecs, dtype=np.float32)
        arr /= (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9)
        return arr

    # ---- search ------------------------------------------------------------
    def _filter_idx(self, filters):
        idx = range(len(self.chunks))
        if not filters:
            return list(idx)
        out = []
        for i in idx:
            m = self.chunks[i]["meta"]
            ok = True
            for k, v in filters.items():
                if v is None:
                    continue
                if isinstance(v, (list, tuple, set)):
                    if m.get(k) not in v:
                        ok = False; break
                elif m.get(k) != v:
                    ok = False; break
            if ok:
                out.append(i)
        return out

    def search(self, query, k=6, filters=None):
        cand = self._filter_idx(filters)
        if not cand:
            return []
        if self.mode == "openai" and self._emb is not None:
            q = self._embed([query])[0]
            sims = self._emb[cand] @ q
            order = np.argsort(-sims)[:k]
            return [{**self.chunks[cand[i]], "score": float(sims[i])} for i in order]
        # BM25-lite
        q_terms = _tok(query)
        N = len(self.chunks)
        scored = []
        for i in cand:
            toks = self._toks[i]
            if not toks:
                continue
            tf = Counter(toks)
            score = 0.0
            for term in q_terms:
                if term not in tf:
                    continue
                idf = math.log(1 + (N - self._df[term] + 0.5) / (self._df[term] + 0.5))
                f = tf[term]
                score += idf * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * len(toks) / self._avg_len))
            if score > 0:
                scored.append((score, i))
        scored.sort(reverse=True)
        return [{**self.chunks[i], "score": float(s)} for s, i in scored[:k]]


_STORE = None


def get_store(chunks=None):
    global _STORE
    if _STORE is None and chunks is not None:
        _STORE = VectorStore().build(chunks)
    return _STORE


if __name__ == "__main__":
    from knowledge.base import build
    kb = build()
    vs = VectorStore().build(kb["chunks"])
    print("mode:", vs.mode, "chunks:", len(vs.chunks))
    for q in ["porosity leak at boss", "spigot diameter oversize tool wear", "coolant concentration"]:
        print(f"\nQ: {q}")
        for r in vs.search(q, k=3):
            print(f"  [{r['score']:.2f}] {r['meta'].get('part_no')}/{r['meta'].get('doc_type')}: {r['text'][:80]}")

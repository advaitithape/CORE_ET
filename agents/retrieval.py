"""Agent 4 — Retrieval / RAG. Semantic search over the knowledge-base chunks."""
from .base import Agent


class RetrievalAgent(Agent):
    name = "retrieval"
    title = "Retrieval / RAG Agent"
    description = "Semantic search over all document text (vector store), with metadata filters."
    uses_llm = True  # via embeddings

    def run(self, query, k=6, part_no=None, doc_type=None, **kw):
        filters = {}
        if part_no:
            filters["part_no"] = part_no
        if doc_type:
            filters["doc_type"] = doc_type
        hits = self.store.search(query, k=k, filters=filters or None) if self.store else []
        return {"query": query, "mode": self.store.mode if self.store else "none",
                "results": [{"text": h["text"], "score": round(h["score"], 3),
                             "meta": h["meta"]} for h in hits]}

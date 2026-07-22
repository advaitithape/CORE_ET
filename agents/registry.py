"""Builds the knowledge base, vector store, and all nine agents as one system.

The knowledge base is INCREMENTAL: it starts from the persisted ingestion manifest
(empty on a clean start) and rebuilds as documents are ingested or the system is reset.
"""
import json
import os

from knowledge.catalog import build_from_ingested, ingest_kind
from knowledge.rag import VectorStore

from .ingestion import IngestionAgent
from .extraction import ExtractionAgent
from .knowledge_graph import KnowledgeGraphAgent
from .retrieval import RetrievalAgent
from .compliance import ComplianceAgent
from .rca import RCAAgent
from .qms import QMSAgent
from .lessons import LessonsAgent
from .copilot import CopilotAgent

MANIFEST = os.path.join("outputs", "ingested.json")


class AgentSystem:
    def __init__(self):
        self.ingested = self._load_manifest()
        self._build()

    # ---- persistence -------------------------------------------------------
    def _load_manifest(self):
        try:
            with open(MANIFEST, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, ValueError):
            return []

    def _save_manifest(self):
        os.makedirs("outputs", exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(self.ingested, f)

    # ---- (re)build ---------------------------------------------------------
    def _build(self):
        self.kb = build_from_ingested(self.ingested)
        self.store = VectorStore().build(self.kb["chunks"])
        self.agents = {}
        for cls in (IngestionAgent, ExtractionAgent, KnowledgeGraphAgent, RetrievalAgent,
                    ComplianceAgent, RCAAgent, QMSAgent, LessonsAgent):
            a = cls(self.kb, self.store)
            self.agents[a.name] = a
        self.agents["copilot"] = CopilotAgent(self.kb, self.store, self.agents)

    # ---- mutation ----------------------------------------------------------
    def ingest(self, basename):
        """Add a document. Returns 'structured', 'general', or None (not ingestable)."""
        if basename in self.ingested:
            return ingest_kind(basename)
        kind = ingest_kind(basename)
        if kind:
            self.ingested.append(basename)
            self._save_manifest()
            self._build()
        return kind

    def reset(self):
        self.ingested = []
        self._save_manifest()
        self._build()

    def catalog(self):
        order = ["ingestion", "extraction", "knowledge_graph", "retrieval", "copilot",
                 "compliance", "rca", "qms", "lessons"]
        return [self.agents[n].meta() for n in order if n in self.agents]


_SYSTEM = None


def get_system():
    global _SYSTEM
    if _SYSTEM is None:
        _SYSTEM = AgentSystem()
    return _SYSTEM


if __name__ == "__main__":
    s = get_system()
    print("ingested:", len(s.ingested), "| RAG:", s.store.mode, "| KB:", json.dumps(s.kb["stats"]))
    print("agents:", len(s.catalog()))

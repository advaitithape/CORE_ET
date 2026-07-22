"""Agent 2 — Extraction. Parses a document into structured entities.

Wraps the deterministic parsers for the known real formats (PFD/PFMEA/Control Plan)
and exposes a uniform extract() for the ingestion pipeline / upload endpoint.
"""
import os
from .base import Agent
from pipeline import parse_pfd, parse_pfmea, parse_control_plan


class ExtractionAgent(Agent):
    name = "extraction"
    title = "Extraction Agent"
    description = "Extracts structured entities & relationships from each document type."

    def extract(self, path, doc_type):
        ext = os.path.splitext(path)[1].lower()
        try:
            if doc_type == "pfmea" and ext == ".xls":
                d = parse_pfmea.parse(path)
                return {"doc_type": doc_type, "entities": len(d["lines"]),
                        "sample": d["lines"][:3]}
            if doc_type == "pfd" and ext == ".xls":
                d = parse_pfd.parse(path)
                return {"doc_type": doc_type, "entities": len(d["operations"]),
                        "sample": d["operations"][:3]}
            if doc_type == "control_plan" and ext == ".xlsx":
                d = parse_control_plan.parse(path)
                return {"doc_type": doc_type, "entities": len(d["controls"]),
                        "sample": d["controls"][:3]}
        except Exception as e:  # noqa: BLE001
            return {"doc_type": doc_type, "error": str(e)}
        return {"doc_type": doc_type, "entities": 0,
                "note": "generated/QMS formats are ingested from canonical records"}

    def run(self, path, doc_type, **kw):
        return self.extract(path, doc_type)

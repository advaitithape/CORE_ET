"""Agent 1 — Ingestion. Accepts a document, classifies its type and routes it.

Two-stage classifier: fast rules on filename/sheet-names first, LLM only when unsure.
"""
import os
from .base import Agent, has_key, llm_chat

DOC_TYPES = ["drawing", "pfd", "pfmea", "control_plan", "inward_inspection",
             "in_process_ir", "pdir", "ncr_car", "capa_8d", "work_instruction", "unknown"]

RULES = [
    ("pfmea", ["pfmea", "fmea"]),
    ("control_plan", ["control plan", "controlplan", "cp/"]),
    ("pfd", ["process flow", "pfd", "flow chart", "flow diagram"]),
    ("inward_inspection", ["inward", "incoming", "qa-05"]),
    ("pdir", ["pdir", "pre despatch", "pre-dispatch", "pre despatch", "qa-03"]),
    ("in_process_ir", ["in-process", "inprocess", "in process", "qa-04", "base ir", "inprocessir"]),
    ("ncr_car", ["ncr", "non conformance", "nonconformance", "car", "qa-01"]),
    ("capa_8d", ["8d", "capa", "qa-02"]),
    ("work_instruction", ["work instruction", "wi ", "si-l-", "sop"]),
    ("drawing", [".pdf"]),
]


class IngestionAgent(Agent):
    name = "ingestion"
    title = "Ingestion Agent"
    description = "Accepts documents, classifies type (rules + LLM), routes to extraction."
    uses_llm = True

    def classify(self, filename, sample_text=""):
        f = (filename or "").lower()
        for dtype, keys in RULES:
            if any(k in f for k in keys):
                return {"doc_type": dtype, "confidence": 0.95, "by": "rules"}
        if has_key() and sample_text:
            try:
                msg = llm_chat(
                    "Classify the industrial document into exactly one of: " + ", ".join(DOC_TYPES) +
                    ". Reply with only the label.",
                    f"Filename: {filename}\nSample:\n{sample_text[:800]}")
                lab = (msg.content or "unknown").strip().split()[0].lower()
                return {"doc_type": lab if lab in DOC_TYPES else "unknown",
                        "confidence": 0.8, "by": "llm"}
            except Exception:  # noqa: BLE001
                pass
        return {"doc_type": "unknown", "confidence": 0.3, "by": "rules"}

    def run(self, filename, sample_text="", **kw):
        res = self.classify(filename, sample_text)
        res["filename"] = os.path.basename(filename or "")
        res["route_to"] = "extraction" if res["doc_type"] != "unknown" else "manual_review"
        return res

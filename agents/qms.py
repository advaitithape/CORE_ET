"""Agent 8 — Quality / QMS. Manages NCR/CAR, 8D CAPA and inspection records, and
generates an audit-ready compliance evidence pack per part."""
from .base import Agent
from pipeline.common import clean


class QMSAgent(Agent):
    name = "qms"
    title = "Quality & QMS Agent"
    description = "Manages non-conformances, 8D CAPAs and inspection reports; builds compliance evidence packs."

    def summary(self, part_no=None):
        out = []
        for p in self.kb["parts"]:
            pno = p["meta"]["part_no"]
            if part_no and pno != part_no:
                continue
            q = p["qms"]
            out.append({
                "part_no": pno, "part_name": p["meta"]["part_name"],
                "ncrs": q.get("ncrs") or [], "capas": q.get("capas") or [],
                "open_ncrs": [n for n in (q.get("ncrs") or []) if n.get("status") == "Open"],
                "inspections": [k for k in ("inward", "inprocess", "pdir") if q.get(k)],
                "work_instruction": bool(q.get("wi")),
            })
        return out

    def evidence_pack(self, part_no):
        """Assemble an audit evidence package linking design → control → inspection → NC → CAPA."""
        p = self.parts().get(part_no)
        if not p:
            return {"error": "unknown part"}
        q = p["qms"]
        return {
            "part": p["meta"],
            "controls": sum(len(o.get("product_chars", []) + o.get("process_chars", []))
                            for o in p["operations"]),
            "high_rpn_failures": [f for f in p["failure_modes"] if (f.get("rpn") or 0) >= 90],
            "inspections_on_file": [k for k in ("inward", "inprocess", "pdir") if q.get(k)],
            "ncrs": q.get("ncrs") or [],
            "capas": q.get("capas") or [],
            "traceability": "design (drawing/PFMEA) → control plan → inspection records → NCR → 8D CAPA",
        }

    def run(self, action="summary", part_no=None, **kw):
        if action == "evidence_pack" and part_no:
            return self.evidence_pack(part_no)
        return {"parts": self.summary(part_no)}

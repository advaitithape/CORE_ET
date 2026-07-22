"""Agent 7 — Maintenance / RCA. Fuses PFMEA, NCR, CAPA and inspection evidence for a
part/operation into a root-cause analysis with a recommended corrective action."""
from .base import Agent, has_key, llm_chat
from pipeline.common import clean


class RCAAgent(Agent):
    name = "rca"
    title = "Maintenance & RCA Agent"
    description = "Root-cause analysis fusing failure history, NCRs, CAPAs and inspection data."
    uses_llm = True

    def _evidence(self, part_no, op_no=None, query=""):
        p = self.parts().get(part_no)
        if not p:
            return None, []
        fms = [f for f in p["failure_modes"] if op_no is None or f.get("op_no") == op_no]
        fms = sorted(fms, key=lambda f: -(f.get("rpn") or 0))[:6]
        ncrs = p["qms"].get("ncrs") or []
        capas = p["qms"].get("capas") or []
        rag = []
        if self.store and query:
            rag = self.store.search(query, k=5, filters={"part_no": part_no})
        return p, {"failures": fms, "ncrs": ncrs, "capas": capas,
                   "rag": [r["text"] for r in rag]}

    def run(self, part_no, op_no=None, problem="", **kw):
        op_no = int(op_no) if op_no not in (None, "", "null") else None
        p, ev = self._evidence(part_no, op_no, problem or "")
        if not p:
            return {"error": "unknown part"}
        if not has_key():
            # deterministic fallback: surface the strongest linked evidence
            top = ev["failures"][0] if ev["failures"] else None
            return {"mode": "fallback", "part_no": part_no, "op_no": op_no,
                    "root_cause": clean(top.get("cause")) if top else "insufficient data",
                    "evidence": ev}
        ctx = self._format(p, ev)
        try:
            msg = llm_chat(
                "You are a senior manufacturing RCA engineer. Use ONLY the evidence provided. "
                "Give: (1) most likely root cause, (2) supporting evidence with citations like "
                "[PFMEA Op X]/[NCR]/[8D], (3) recommended corrective + preventive action. Be concise.",
                f"PART {part_no} {p['meta']['part_name']}"
                + (f", OPERATION {op_no}" if op_no else "")
                + (f"\nPROBLEM: {problem}" if problem else "")
                + f"\n\nEVIDENCE:\n{ctx}")
            return {"mode": "openai", "part_no": part_no, "op_no": op_no,
                    "analysis": msg.content, "evidence": ev}
        except Exception as e:  # noqa: BLE001
            return {"mode": "error", "error": str(e), "evidence": ev}

    def _format(self, p, ev):
        lines = ["Failure modes:"]
        for f in ev["failures"]:
            lines.append(f"  - Op {f.get('op_no')}: {clean(f.get('failure_mode'))} | cause {clean(f.get('cause'))} "
                         f"| RPN {f.get('rpn')} | action {clean(f.get('recommended_action')) or 'none'}")
        lines.append("NCRs:")
        for n in ev["ncrs"]:
            lines.append(f"  - {clean(n.get('reason'))} ({n.get('rej_pct')}% rej) → {clean(n.get('corrective_action'))}")
        lines.append("8D CAPAs:")
        for c in ev["capas"]:
            lines.append(f"  - {c.get('notification_no')}: root cause {clean(c.get('root_cause'))}")
        if ev["rag"]:
            lines.append("Related records:")
            lines += [f"  - {t}" for t in ev["rag"]]
        return "\n".join(lines)

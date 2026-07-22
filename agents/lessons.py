"""Agent 9 — Lessons Learned / Failure Intelligence.

Mines failure modes, NCRs and CAPAs across ALL parts to surface systemic patterns
that are invisible to any single part or review — and pushes proactive warnings.
"""
import re
from collections import defaultdict
from .base import Agent, has_key, llm_chat
from pipeline.common import clean

_STOP = set("the a an of to in on at for and or not as per is are with from into no".split())
_TOK = re.compile(r"[a-z]+")


def _keywords(text):
    return [w for w in _TOK.findall((text or "").lower()) if w not in _STOP and len(w) > 3]


class LessonsAgent(Agent):
    name = "lessons"
    title = "Lessons Learned / Failure Intelligence Agent"
    description = "Finds systemic failure patterns across all parts and pushes proactive warnings."
    uses_llm = True

    def patterns(self):
        # cluster failure modes + NCR reasons by shared keyword across parts
        byword = defaultdict(list)
        for p in self.kb["parts"]:
            pno = p["meta"]["part_no"]
            for f in p["failure_modes"]:
                for w in set(_keywords(f.get("failure_mode")) + _keywords(f.get("cause"))):
                    byword[w].append({"part_no": pno, "op": f.get("op_no"),
                                      "text": clean(f.get("failure_mode")), "rpn": f.get("rpn"),
                                      "kind": "failure"})
            for ncr in p["qms"].get("ncrs") or []:
                for w in set(_keywords(ncr.get("reason"))):
                    byword[w].append({"part_no": pno, "text": clean(ncr.get("reason")),
                                      "kind": "ncr", "rej_pct": ncr.get("rej_pct")})
        pats = []
        for w, items in byword.items():
            parts_hit = {i["part_no"] for i in items}
            if len(parts_hit) >= 2 and len(items) >= 3:
                pats.append({"theme": w, "parts": sorted(parts_hit),
                             "count": len(items), "examples": items[:6]})
        pats.sort(key=lambda x: (-len(x["parts"]), -x["count"]))
        return pats[:8]

    def warnings(self):
        """Proactive warnings: a fault seen on one part whose conditions exist on another."""
        warns = []
        pats = self.patterns()
        for p in pats:
            if len(p["parts"]) >= 2:
                warns.append(
                    f"Theme '{p['theme']}' recurs on parts {', '.join(p['parts'])} "
                    f"({p['count']} records) — treat as a cross-part systemic risk, not isolated incidents.")
        return warns

    def run(self, explain=False, **kw):
        pats = self.patterns()
        result = {"patterns": pats, "warnings": self.warnings()}
        if explain and has_key() and pats:
            brief = "\n".join(f"- theme '{p['theme']}' on {p['parts']} ({p['count']} records)" for p in pats[:6])
            try:
                msg = llm_chat(
                    "You are a manufacturing failure-intelligence analyst. Be concise and concrete.",
                    f"Across our parts we detected these recurring themes:\n{brief}\n\n"
                    "Summarise the top 3 systemic risks and one proactive action each. Cite part numbers.")
                result["narrative"] = msg.content
            except Exception as e:  # noqa: BLE001
                result["narrative_error"] = str(e)
        return result

"""Agent 6 — Compliance & Gap Detection.

Runs a rules engine over the multi-part knowledge base and returns ranked, cited
findings. Deterministic (no LLM needed); the copilot/LLM only phrases explanations.
"""
import re
from .base import Agent
from pipeline.common import clean, parse_spec

RPN_THRESHOLD = 90
_TOK = re.compile(r"[a-z0-9]+")


def _norm(s):
    return set(_TOK.findall((s or "").lower()))


def _to_float(x):
    try:
        return float(str(x).strip())
    except (ValueError, TypeError):
        return None


class ComplianceAgent(Agent):
    name = "compliance"
    title = "Compliance & Gap Detection Agent"
    description = "Detects cross-document quality & compliance gaps (C1–C10) across the knowledge graph."

    def run(self, part_no=None, **kw):
        findings = []
        n = [0]

        def add(check, sev, part, title, detail, evidence, fix):
            n[0] += 1
            findings.append({"id": f"F{n[0]:03d}", "check": check, "severity": sev,
                             "part_no": part, "title": title, "detail": detail,
                             "evidence": evidence, "suggested_fix": fix})

        for p in self.kb["parts"]:
            pno = p["meta"]["part_no"]
            if part_no and pno != part_no:
                continue
            ops = {o["op_no"]: o for o in p["operations"] if o.get("op_no")}
            fms = p["failure_modes"]
            fm_ops = {f["op_no"] for f in fms if f.get("op_no")}

            # C3 — unmitigated high-RPN
            hi = [f for f in fms if (f.get("rpn") or 0) >= RPN_THRESHOLD and not clean(f.get("recommended_action"))]
            for f in sorted(hi, key=lambda x: -(x.get("rpn") or 0))[:5]:
                add("C3", "high", pno,
                    f"[{pno}] High-RPN failure with no action: {clean(f['failure_mode'])} (RPN {int(f['rpn'])})",
                    f"Op {f['op_no']} failure mode has S{f.get('severity')}/O{f.get('occurrence')}/D{f.get('detection_val')}, "
                    f"RPN {int(f['rpn'])}, but no recommended action.",
                    [{"doc": "PFMEA", "part_no": pno, "op": f["op_no"]}],
                    "Assign a recommended action, owner and target date.")

            # C2 — operation with failure modes but no controls
            for opn in sorted(fm_ops):
                op = ops.get(opn)
                if op and not (op.get("product_chars") or op.get("process_chars")):
                    add("C2", "high", pno,
                        f"[{pno}] Operation {opn} has failure modes but no controls",
                        f"PFMEA defines failure modes for Op {opn} but the Control Plan has no controls for it.",
                        [{"doc": "PFMEA", "part_no": pno, "op": opn}],
                        "Add Control Plan entries covering detection/prevention.")

            # C8 — systemic root cause across operations
            groups = {}
            for f in fms:
                if (f.get("rpn") or 0) >= RPN_THRESHOLD and clean(f.get("cause")):
                    groups.setdefault(clean(f["cause"]).lower()[:45], []).append(f)
            for key, g in groups.items():
                opset = sorted({f["op_no"] for f in g})
                if len(g) >= 3 and len(opset) >= 2:
                    add("C8", "high", pno,
                        f"[{pno}] Systemic root cause across {len(opset)} operations: \"{clean(g[0]['cause'])[:45]}\"",
                        f"The cause drives {len(g)} high-RPN failures across Ops {', '.join(map(str, opset))} — "
                        f"invisible in single-operation review.",
                        [{"doc": "PFMEA", "part_no": pno, "op": o} for o in opset[:5]],
                        "Address as one systemic corrective action.")

            # C10 — measured observation out of specification (inspection vs control tolerance)
            limits = self._char_limits(p)
            for rec, dt in self._inspection_records(p):
                for item in rec:
                    name = item.get("param") or item.get("char") or ""
                    lo, hi, spec = self._match_limits(name, limits, item.get("spec"))
                    if lo is None and hi is None:
                        continue
                    for obs in item.get("obs", []) + ([item.get("first")] if item.get("first") else []):
                        v = _to_float(obs)
                        if v is None:
                            continue
                        if (lo is not None and v < lo) or (hi is not None and v > hi):
                            add("C10", "high", pno,
                                f"[{pno}] Out-of-spec measurement: {name} = {v} (spec {spec})",
                                f"In {dt}, {name} measured {v}, outside specification {spec} "
                                f"[{lo}–{hi}]. A recorded nonconformance escaped as a data point.",
                                [{"doc": dt, "part_no": pno, "note": name}],
                                "Raise/verify an NCR for this reading and check the control at that operation.")
                            break

            # C9 — open NCR without a linked CAPA
            capa_ids = " ".join(c.get("notification_no", "") for c in (p["qms"].get("capas") or []))
            for ncr in p["qms"].get("ncrs") or []:
                if ncr.get("status") == "Open" and "NCR-" not in (ncr.get("corrective_action") or "") \
                        and ncr.get("reason", "") not in capa_ids:
                    linked = any(cid in (ncr.get("corrective_action") or "") for cid in
                                 [c.get("notification_no", "") for c in (p["qms"].get("capas") or [])])
                    if not linked:
                        add("C9", "medium", pno,
                            f"[{pno}] Open NCR without a linked 8D/CAPA: {clean(ncr['reason'])[:40]}",
                            f"NCR (SL {ncr['sl']}, {ncr['rej_pct']}% reject) is open but not linked to an 8D CAPA.",
                            [{"doc": "NCR/CAR", "part_no": pno}],
                            "Open an 8D CAPA and link it to this NCR.")

        order = {"high": 0, "medium": 1, "low": 2, "info": 3}
        cprio = {"C10": 0, "C8": 1, "C2": 2, "C3": 3, "C9": 4, "C6": 5}
        findings.sort(key=lambda f: (order.get(f["severity"], 9), cprio.get(f["check"], 9)))
        summary = {}
        for f in findings:
            summary[f["severity"]] = summary.get(f["severity"], 0) + 1
        return {"findings": findings, "summary": summary, "total": len(findings)}

    # -- helpers --
    def _char_limits(self, part):
        out = {}
        for o in part["operations"]:
            for ch in o.get("product_chars", []) + o.get("process_chars", []):
                lo, hi = ch.get("low"), ch.get("high")
                if lo is None and hi is None:
                    ps = parse_spec(ch.get("spec"))
                    if ps:
                        lo, hi = ps.get("low"), ps.get("high")
                out[ch.get("name", "")] = (lo, hi, ch.get("spec", ""))
        return out

    def _match_limits(self, name, limits, own_spec):
        # trust the inspection line's own spec first (it is authoritative for that reading)
        ps = parse_spec(own_spec)
        if ps and (ps.get("low") is not None or ps.get("high") is not None):
            return ps.get("low"), ps.get("high"), own_spec
        # else fall back to the matched control-plan tolerance (e.g. nominal-only specs)
        nt = _norm(name)
        best, score = None, 0
        for cname, val in limits.items():
            ov = len(nt & _norm(cname))
            if ov > score:
                score, best = ov, val
        if best and score >= 1 and (best[0] is not None or best[1] is not None):
            return best
        return None, None, own_spec

    def _inspection_records(self, part):
        q = part["qms"]
        recs = []
        if q.get("inprocess"):
            recs.append((q["inprocess"]["params"], "In-Process IR"))
        if q.get("pdir"):
            recs.append((q["pdir"]["chars"], "PDIR"))
        if q.get("inward"):
            recs.append((q["inward"]["params"], "Inward Inspection"))
        return recs

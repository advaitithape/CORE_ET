"""Unified multi-part knowledge base.

Loads Part 1 (CE21609) from its real files via the existing parsers, and Parts 2 & 3
from the canonical dataset, into one uniform structure. Produces:
  - a knowledge GRAPH (Part → Operation → FailureMode / Control, plus QMS nodes)
  - retrieval CHUNKS (one per record) for the RAG store
  - QMS records (inspections, NCR/CAR, 8D CAPA) indexed by part
Every node/chunk keeps a source citation.
"""
import os

from pipeline import parse_pfd, parse_pfmea, parse_control_plan
from pipeline.common import clean, parse_spec
from dataset import parts as P

# CE21609 source files, located at runtime in data/ OR data/uploads/ — so a deployed
# instance ships with NO data and works entirely from documents uploaded by the user.
CE_FILES = {
    "pfd": "CE21609_ Process Flow Chart 2.xls",
    "pfmea": "CE21609_ PFMEA 2.xls",
    "cp": "CE21609_CONTROL PLAN 2.xlsx",
}


def find_file(basename):
    """Resolve a document by basename across data/ and data/uploads/."""
    for root in ("data", os.path.join("data", "uploads")):
        p = os.path.join(root, basename)
        if os.path.exists(p):
            return p
    return None


# ---- canonical part builders ------------------------------------------------

def _ce21609_canonical():
    """Build CE21609 from its real files. Returns None when the files are not present
    (e.g. a fresh deployment) — the part becomes available once they are uploaded."""
    paths = {k: find_file(v) for k, v in CE_FILES.items()}
    if not any(paths.values()):
        return None
    try:
        pfd = parse_pfd.parse(paths["pfd"]) if paths["pfd"] else {"meta": {}, "operations": []}
        pfmea = parse_pfmea.parse(paths["pfmea"]) if paths["pfmea"] else {"lines": []}
        cp = parse_control_plan.parse(paths["cp"]) if paths["cp"] else {"sheets": [], "controls": []}
    except Exception:  # noqa: BLE001 — corrupt/partial upload must not kill the system
        return None
    ops = {}
    for o in pfd["operations"]:
        if o["op_no"] and o["op_no"] > 0:
            ops.setdefault(o["op_no"], {"op_no": o["op_no"], "name": o["name"],
                                        "machine": "", "cp_ref": o["cp_ref"],
                                        "product_chars": [], "process_chars": []})
    for c in cp["controls"]:
        if c["op_no"] in ops:
            ops[c["op_no"]]["product_chars"].append({
                "name": c["characteristic"], "spec": c["specification"],
                "special": c["special"], "unit": "",
                "measurement_method": c["measurement_method"],
                "frequency": c["frequency"], "reaction_plan": c["reaction_plan"]})
    fms = []
    for l in pfmea["lines"]:
        if l["op_no"] and l["op_no"] > 0:
            fms.append({"op_no": l["op_no"], "function": l["function"],
                        "failure_mode": l["failure_mode"], "effect": l["effect"],
                        "severity": l["severity"], "cause": l["cause"],
                        "occurrence": l["occurrence"], "prevention": l["prevention"],
                        "detection": l["detection"], "detection_val": l["detection_val"],
                        "rpn": l["rpn"], "recommended_action": l["recommended_action"]})
    return {
        "meta": {"part_no": "CE21609", "part_name": pfd["meta"].get("part_name", "Pinion Shaft"),
                 "customer": "Agri-Equipment OEM", "supplier": "Precision Machining Plant",
                 "material": "SAE 8620 (Alloy Steel)", "process_type": "Machining"},
        "operations": list(ops.values()), "failure_modes": fms,
    }


def _from_canonical(part):
    return {
        "meta": {"part_no": part["part_no"], "part_name": part["part_name"],
                 "customer": part["customer"], "supplier": part["supplier"],
                 "material": part["material"], "process_type": part["process_type"]},
        "operations": part["operations"], "failure_modes": part["failure_modes"],
    }


def _attach_qms(part_no):
    q = {"inward": P.INWARD.get(part_no), "inprocess": P.INPROCESS.get(part_no),
         "pdir": P.PDIR.get(part_no),
         "ncrs": [n for n in P.NCRS if n["part_no"] == part_no],
         "capas": [c for c in P.CAPAS if c["part_no"] == part_no]}
    wi = P.PARTS.get(part_no, {}).get("wi")
    if part_no == "S-10254-5":
        wi = P.BASE["wi"]
    q["wi"] = wi
    return q


def load_parts():
    parts = [_ce21609_canonical(), _from_canonical(P.BASE), _from_canonical(P.YOKE)]
    parts = [p for p in parts if p is not None]
    for p in parts:
        p["qms"] = _attach_qms(p["meta"]["part_no"])
    return parts


# ---- graph + chunks ---------------------------------------------------------

def build():
    """Full knowledge base from all three demo parts (used for tests/tools)."""
    return build_graph_from_parts(load_parts())


def build_graph_from_parts(parts):
    """Build the graph + RAG chunks + stats from a list of canonical parts.
    Accepts any subset (including an empty list) so the KB can grow incrementally."""
    nodes, edges, chunks = [], [], []

    def node(nid, ntype, label, attrs, source, part_no):
        nodes.append({"id": nid, "type": ntype, "label": label, "attrs": attrs,
                      "source": source, "part_no": part_no})

    def edge(s, t, et):
        edges.append({"source": s, "target": t, "type": et})

    def chunk(cid, text, meta):
        chunks.append({"id": cid, "text": text, "meta": meta})

    for p in parts:
        m = p["meta"]; pno = m["part_no"]
        pid = f"part:{pno}"
        node(pid, "Part", f"{m['part_name']} ({pno})", m, {"doc": "Master"}, pno)
        chunk(f"c:{pid}", f"Part {pno} {m['part_name']}, customer {m['customer']}, "
              f"supplier {m['supplier']}, material {m['material']}, process {m['process_type']}.",
              {"part_no": pno, "doc_type": "part", "op_no": None})

        opidx = {}
        for o in p["operations"]:
            if not o.get("op_no"):
                continue
            oid = f"op:{pno}:{o['op_no']}"
            opidx[o["op_no"]] = oid
            node(oid, "Operation", f"{o['op_no']} · {o['name']}",
                 {"op_no": o["op_no"], "machine": o.get("machine", ""), "cp_ref": o.get("cp_ref")},
                 {"doc": "PFD"}, pno)
            edge(pid, oid, "HAS_OPERATION")
            for i, ch in enumerate(o.get("product_chars", []) + o.get("process_chars", [])):
                cid = f"ctrl:{pno}:{o['op_no']}:{i}"
                spec = ch.get("spec", "")
                node(cid, "Control", clean(ch.get("name", ""))[:60],
                     {"characteristic": ch.get("name"), "specification": spec,
                      "special": ch.get("special", ""), "unit": ch.get("unit", ""),
                      "measurement_method": ch.get("measurement_method", ""),
                      "frequency": ch.get("frequency", ""),
                      "reaction_plan": ch.get("reaction_plan", ""),
                      **{k: ch[k] for k in ("low", "high", "nominal") if k in ch}},
                     {"doc": "ControlPlan", "op": o["op_no"]}, pno)
                edge(oid, cid, "CONTROLLED_BY")
                chunk(f"c:{cid}", f"[{pno} Op {o['op_no']} {o['name']}] Control: "
                      f"{ch.get('name')} spec {spec} {ch.get('special','')}".strip(),
                      {"part_no": pno, "doc_type": "control_plan", "op_no": o["op_no"]})

        for i, f in enumerate(p["failure_modes"]):
            if not f.get("op_no"):
                continue
            oid = opidx.get(f["op_no"])
            if not oid:
                continue
            fid = f"fm:{pno}:{f['op_no']}:{i}"
            node(fid, "FailureMode", (clean(f.get("failure_mode")) or clean(f.get("cause")))[:60],
                 {k: f.get(k) for k in ("failure_mode", "effect", "severity", "cause",
                  "occurrence", "detection", "detection_val", "rpn", "recommended_action")},
                 {"doc": "PFMEA", "op": f["op_no"]}, pno)
            edge(oid, fid, "CAN_FAIL")
            chunk(f"c:{fid}", f"[{pno} Op {f['op_no']}] Failure mode: {f.get('failure_mode')}; "
                  f"effect {f.get('effect')}; cause {f.get('cause')}; "
                  f"S{f.get('severity')} O{f.get('occurrence')} D{f.get('detection_val')} "
                  f"RPN {f.get('rpn')}; action {f.get('recommended_action') or 'none'}.",
                  {"part_no": pno, "doc_type": "pfmea", "op_no": f["op_no"], "rpn": f.get("rpn")})

        # ---- QMS nodes + chunks ----
        q = p["qms"]
        for n in q.get("ncrs") or []:
            nid = f"ncr:{pno}:{n['sl']}"
            node(nid, "NCR", f"NCR-{pno}-{n['sl']} · {n['reason'][:30]}", n,
                 {"doc": "NCR/CAR"}, pno)
            edge(pid, nid, "HAS_NCR")
            chunk(f"c:{nid}", f"[{pno} NCR {n['sl']} {n['month']}] {n['reason']}; "
                  f"in-process rej {n['inprocess_rej']}, PDI rej {n['pdi_rej']}, {n['rej_pct']}%; "
                  f"corrective action: {n['corrective_action']}; status {n['status']}.",
                  {"part_no": pno, "doc_type": "ncr", "op_no": None})
        for c in q.get("capas") or []:
            cid = f"capa:{pno}:{c['notification_no']}"
            node(cid, "CAPA", f"8D {c['notification_no']}", c, {"doc": "8D CAPA"}, pno)
            edge(pid, cid, "HAS_CAPA")
            chunk(f"c:{cid}", f"[{pno} 8D {c['notification_no']}] problem: {c['problem']['what']}; "
                  f"root cause: {c['root_cause']}; corrective action: {c['corrective_action']}; "
                  f"preventive: {c['preventive_action']}; status {c['status']}.",
                  {"part_no": pno, "doc_type": "capa", "op_no": None})
        for key, dt in (("inward", "inward_inspection"), ("pdir", "pdir")):
            rec = q.get(key)
            if not rec:
                continue
            rid = f"insp:{pno}:{key}"
            node(rid, "Inspection", f"{dt.replace('_',' ').title()} · {pno}",
                 {"kind": dt, **{k: v for k, v in rec.items() if k != "params" and k != "chars"}},
                 {"doc": dt}, pno)
            edge(pid, rid, "HAS_INSPECTION")
            items = rec.get("params") or rec.get("chars") or []
            body = "; ".join(f"{it.get('param') or it.get('char')} spec {it.get('spec')} "
                             f"obs {','.join(map(str, it.get('obs', [])))}" for it in items)
            chunk(f"c:{rid}", f"[{pno} {dt}] {body}. status {rec.get('status','')}.",
                  {"part_no": pno, "doc_type": dt, "op_no": None})
        ip = q.get("inprocess")
        if ip:
            rid = f"insp:{pno}:inprocess"
            node(rid, "Inspection", f"In-Process IR · Op {ip['op_no']}",
                 {"kind": "in_process", "op_no": ip["op_no"], "date": ip["date"]},
                 {"doc": "in_process", "op": ip["op_no"]}, pno)
            oid = opidx.get(ip["op_no"], pid)
            edge(oid, rid, "HAS_INSPECTION")
            body = "; ".join(f"{it['param']} spec {it['spec']} obs {','.join(map(str, it['obs']))}"
                             for it in ip["params"])
            chunk(f"c:{rid}", f"[{pno} in-process Op {ip['op_no']}] {body}.",
                  {"part_no": pno, "doc_type": "in_process", "op_no": ip["op_no"]})
        wi = q.get("wi")
        if wi:
            wid = f"wi:{pno}"
            steps = wi.get("steps_en", [])
            node(wid, "WorkInstruction", wi.get("title", "Work Instruction"),
                 {"op_no": wi.get("op_no"), "language": wi.get("language"),
                  "steps": steps, "source_file": wi.get("source_file", "")},
                 {"doc": "WorkInstruction", "op": wi.get("op_no")}, pno)
            oid = opidx.get(wi.get("op_no"), pid)
            edge(oid, wid, "HAS_WORK_INSTRUCTION")
            chunk(f"c:{wid}", f"[{pno} Work Instruction Op {wi.get('op_no')} ({wi.get('language')})] "
                  + " ".join(steps), {"part_no": pno, "doc_type": "work_instruction",
                                       "op_no": wi.get("op_no")})

    stats = {"parts": len(parts),
             "operations": sum(1 for n in nodes if n["type"] == "Operation"),
             "failure_modes": sum(1 for n in nodes if n["type"] == "FailureMode"),
             "controls": sum(1 for n in nodes if n["type"] == "Control"),
             "ncrs": sum(1 for n in nodes if n["type"] == "NCR"),
             "capas": sum(1 for n in nodes if n["type"] == "CAPA"),
             "inspections": sum(1 for n in nodes if n["type"] == "Inspection"),
             "nodes": len(nodes), "edges": len(edges), "chunks": len(chunks)}
    return {"parts": parts, "nodes": nodes, "edges": edges, "chunks": chunks, "stats": stats}


if __name__ == "__main__":
    import json
    kb = build()
    print(json.dumps(kb["stats"], indent=2))

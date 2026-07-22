"""Agent 5 — Copilot Orchestrator.

The conversational brain. With an OpenAI key it runs an agentic tool-calling loop:
the model chooses which specialist agent to invoke (RAG search, graph lookup,
compliance, RCA, QMS, lessons), executes it, and composes a cited answer.
Without a key it falls back to RAG + graph grounding.
"""
import json
import os
from .base import Agent, has_key

TOOLS = [
    {"type": "function", "function": {
        "name": "search_documents",
        "description": "Semantic search over ALL ingested documents (PFMEA, control plans, inspections, NCRs, CAPAs, work instructions). Use for 'what/why/how' and free-text questions.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
            "part_no": {"type": "string", "description": "optional filter e.g. CE21609, S-10254-5, YF-4021"},
        }, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_operation_details",
        "description": "Get the full digital thread for one operation of a part: its controls, failure modes and inspections.",
        "parameters": {"type": "object", "properties": {
            "part_no": {"type": "string"}, "op_no": {"type": "integer"}}, "required": ["part_no", "op_no"]}}},
    {"type": "function", "function": {
        "name": "detect_compliance_gaps",
        "description": "Run the consistency/compliance auditor and return ranked gaps (out-of-spec, unmitigated risk, systemic causes, missing controls).",
        "parameters": {"type": "object", "properties": {"part_no": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "root_cause_analysis",
        "description": "Fuse failure history, NCRs, CAPAs and inspection data into a root-cause analysis for a part/operation/problem.",
        "parameters": {"type": "object", "properties": {
            "part_no": {"type": "string"}, "op_no": {"type": "integer"}, "problem": {"type": "string"}},
            "required": ["part_no"]}}},
    {"type": "function", "function": {
        "name": "qms_status",
        "description": "Get quality status for a part: open NCRs, 8D CAPAs, inspections on file.",
        "parameters": {"type": "object", "properties": {"part_no": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "failure_patterns",
        "description": "Find systemic failure patterns recurring ACROSS parts and proactive warnings.",
        "parameters": {"type": "object", "properties": {}}}},
]

SYSTEM = (
    "You are the Industrial Knowledge Copilot for a factory quality team. You answer "
    "operational, maintenance, quality and compliance questions about manufactured parts "
    "(e.g. CE21609 Pinion Shaft, S-10254-5 Base casting, YF-4021 Yoke Flange). "
    "The knowledge base may ALSO contain general uploaded documents (reports, notes, "
    "finance sheets, essays…) — when a question concerns those, use search_documents and "
    "cite the filename, e.g. [myreport.pdf]. "
    "ALWAYS ground answers in tool results and cite sources like [PFMEA Op 60], "
    "[NCR], [8D NCR-YF-007], [Control Plan], [In-Process IR], or [filename] for general "
    "documents. Prefer calling a tool over guessing. Be concise and practical, like a "
    "senior quality engineer. If the knowledge base holds nothing relevant, say so plainly."
)


class CopilotAgent(Agent):
    name = "copilot"
    title = "Copilot Orchestrator Agent"
    description = "Conversational brain; routes questions to specialist agents via tool-calling."
    uses_llm = True

    def __init__(self, kb, store, registry):
        super().__init__(kb, store)
        self.reg = registry  # dict of name -> agent instance

    def _dispatch(self, name, args):
        try:
            if name == "search_documents":
                return self.reg["retrieval"].run(query=args["query"], part_no=args.get("part_no"), k=6)
            if name == "get_operation_details":
                return {"nodes": self.reg["knowledge_graph"].operation(args["part_no"], int(args["op_no"]))}
            if name == "detect_compliance_gaps":
                return self.reg["compliance"].run(part_no=args.get("part_no"))
            if name == "root_cause_analysis":
                return self.reg["rca"].run(part_no=args["part_no"], op_no=args.get("op_no"),
                                           problem=args.get("problem", ""))
            if name == "qms_status":
                return self.reg["qms"].run(part_no=args.get("part_no"))
            if name == "failure_patterns":
                return self.reg["lessons"].run()
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)}
        return {"error": "unknown tool"}

    def run(self, message, history=None, **kw):
        if not has_key():
            return self._fallback(message)
        from openai import OpenAI
        client = OpenAI()
        model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o")
        msgs = [{"role": "system", "content": SYSTEM}]
        # carry prior conversation turns so the copilot holds context
        for h in (history or [])[-8:]:
            if h.get("role") in ("user", "assistant") and h.get("content"):
                msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": message})
        trace = []
        try:
            for _ in range(5):
                resp = client.chat.completions.create(
                    model=model, messages=msgs, tools=TOOLS, tool_choice="auto", temperature=0.1)
                m = resp.choices[0].message
                if not m.tool_calls:
                    return {"mode": "agentic", "answer": m.content, "tools_used": trace}
                msgs.append({"role": "assistant", "content": m.content or "",
                             "tool_calls": [tc.model_dump() for tc in m.tool_calls]})
                for tc in m.tool_calls:
                    args = json.loads(tc.function.arguments or "{}")
                    result = self._dispatch(tc.function.name, args)
                    trace.append({"tool": tc.function.name, "args": args})
                    msgs.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": json.dumps(result, default=str)[:6000]})
            # ran out of iterations — final synthesis
            resp = client.chat.completions.create(model=model, messages=msgs, temperature=0.1)
            return {"mode": "agentic", "answer": resp.choices[0].message.content, "tools_used": trace}
        except Exception as e:  # noqa: BLE001
            out = self._fallback(message)
            out["error"] = str(e)
            return out

    def _fallback(self, message):
        hits = self.store.search(message, k=5) if self.store else []
        if not hits:
            return {"mode": "fallback", "answer": "No matching records found. (Set OPENAI_API_KEY for full agentic answers.)", "tools_used": []}
        lines = ["Grounded from the knowledge base (set OPENAI_API_KEY for full conversational answers):", ""]
        for h in hits:
            m = h["meta"]
            lines.append(f"- [{m.get('part_no')} · {m.get('doc_type')}"
                         + (f" Op {m.get('op_no')}" if m.get('op_no') else "") + f"] {h['text'][:160]}")
        return {"mode": "fallback", "answer": "\n".join(lines),
                "tools_used": [{"tool": "search_documents", "args": {"query": message}}]}

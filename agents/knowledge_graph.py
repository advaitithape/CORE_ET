"""Agent 3 — Knowledge Graph. Serves the graph and answers structural traversals."""
from .base import Agent


class KnowledgeGraphAgent(Agent):
    name = "knowledge_graph"
    title = "Knowledge Graph Agent"
    description = "Builds and traverses the unified graph (parts, operations, controls, failures, QMS)."

    def graph(self, part_no=None):
        if not part_no:
            return {"nodes": self.kb["nodes"], "edges": self.kb["edges"], "stats": self.kb["stats"]}
        keep = {n["id"] for n in self.kb["nodes"] if n.get("part_no") == part_no}
        nodes = [n for n in self.kb["nodes"] if n["id"] in keep]
        edges = [e for e in self.kb["edges"] if e["source"] in keep and e["target"] in keep]
        return {"nodes": nodes, "edges": edges}

    def operation(self, part_no, op_no):
        """Everything attached to one operation — the digital thread for a step."""
        oid = f"op:{part_no}:{op_no}"
        adj = [e for e in self.kb["edges"] if e["source"] == oid or e["target"] == oid]
        ids = {oid} | {e["target"] for e in adj} | {e["source"] for e in adj}
        return [n for n in self.kb["nodes"] if n["id"] in ids]

    def run(self, part_no=None, op_no=None, **kw):
        if op_no is not None and part_no:
            return {"nodes": self.operation(part_no, int(op_no))}
        return self.graph(part_no)

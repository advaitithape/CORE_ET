"""FastAPI backend — Industrial Knowledge Intelligence platform.

The knowledge base is INCREMENTAL: it boots empty (clean start) and grows as documents
are ingested (via the catalog 'Add' action or an upload) and can be reset to zero.
"""
import os
import shutil
import sys

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.registry import get_system          # noqa: E402
from agents.base import has_key                  # noqa: E402
from knowledge.catalog import KNOWN_DOCS         # noqa: E402

app = FastAPI(title="Industrial Knowledge Intelligence API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SYS = get_system()
UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _resolve_paths():
    """Map basename -> on-disk path across data/, data/generated/, data/uploads/."""
    out = {}
    for root in ("data",):
        for dp, _, files in os.walk(root):
            for fn in files:
                if fn.startswith("~$") or fn.endswith((".py", ".json")):
                    continue
                out.setdefault(fn, os.path.join(dp, fn))
    return out


def _infer_part(fn):
    f = fn.upper()
    if "CE21609" in f: return "CE21609"
    if "S-10254" in f or "BASE" in f: return "S-10254-5"
    if "YF-4021" in f or "YOKE" in f: return "YF-4021"
    return None


class ChatReq(BaseModel):
    message: str
    history: list[dict] = []


class RCAReq(BaseModel):
    part_no: str
    op_no: int | None = None
    problem: str = ""


class IngestReq(BaseModel):
    basename: str


def _stats():
    return {"stats": SYS.kb["stats"], "ingested": SYS.ingested,
            "rag_mode": SYS.store.mode, "parts": [p["meta"] for p in SYS.kb["parts"]]}


@app.get("/api/health")
def health():
    return {"ok": True, "llm_key": has_key(), "rag_mode": SYS.store.mode,
            "ingested": len(SYS.ingested), "stats": SYS.kb["stats"]}


@app.get("/api/system")
def system():
    return {"stats": SYS.kb["stats"], "rag_mode": SYS.store.mode, "llm_key": has_key(),
            "agents": SYS.catalog(), "ingested_count": len(SYS.ingested),
            "parts": [p["meta"] for p in SYS.kb["parts"]]}


@app.get("/api/parts")
def parts():
    out = []
    for p in SYS.kb["parts"]:
        m = dict(p["meta"])
        m["operations"] = len(p["operations"])
        m["failure_modes"] = len(p["failure_modes"])
        m["open_ncrs"] = len([n for n in (p["qms"].get("ncrs") or []) if n.get("status") == "Open"])
        out.append(m)
    return {"parts": out}


@app.get("/api/catalog")
def catalog():
    """All known demo documents, with whether each has been ingested."""
    paths = _resolve_paths()
    rows = []
    for bn, (part, dtype) in KNOWN_DOCS.items():
        rows.append({"name": bn, "part_no": part, "doc_type": dtype,
                     "ingested": bn in SYS.ingested, "available": bn in paths})
    rows.sort(key=lambda r: (r["part_no"], r["name"]))
    return {"documents": rows, "ingested_count": len(SYS.ingested), "total": len(rows)}


@app.get("/api/documents")
def documents():
    """Only the documents that have actually been ingested (the working set)."""
    paths = _resolve_paths()
    out = []
    for bn in SYS.ingested:
        part, dtype = KNOWN_DOCS.get(bn, (_infer_part(bn), "general"))
        p = paths.get(bn)
        out.append({"name": bn, "doc_type": dtype, "part_no": part,
                    "size_kb": round(os.path.getsize(p) / 1024, 1) if p else None,
                    "source": "real" if p and "generated" not in p and "uploads" not in p
                              else ("generated" if p and "generated" in p else "upload")})
    return {"documents": out}


@app.get("/api/graph")
def graph(part_no: str | None = None):
    return SYS.agents["knowledge_graph"].run(part_no=part_no)


@app.get("/api/findings")
def findings(part_no: str | None = None):
    return SYS.agents["compliance"].run(part_no=part_no)


@app.get("/api/qms")
def qms(part_no: str | None = None):
    return SYS.agents["qms"].run(part_no=part_no)


@app.get("/api/lessons")
def lessons(explain: bool = False):
    return SYS.agents["lessons"].run(explain=explain)


@app.post("/api/rca")
def rca(req: RCAReq):
    return SYS.agents["rca"].run(part_no=req.part_no, op_no=req.op_no, problem=req.problem)


@app.post("/api/chat")
def chat(req: ChatReq):
    return SYS.agents["copilot"].run(message=req.message, history=req.history)


@app.post("/api/ingest")
def ingest(req: IngestReq):
    ok = SYS.ingest(req.basename)
    return {"ok": ok, "basename": req.basename, **_stats()}


@app.post("/api/reset")
def reset():
    SYS.reset()
    return {"ok": True, **_stats()}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), part_no: str = Form(default="")):
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    cls = SYS.agents["ingestion"].run(filename=file.filename)
    kind = SYS.ingest(file.filename)
    if kind == "general":
        cls["doc_type"] = "general"
    notes = {"structured": "Ingested — structured data merged into the knowledge graph.",
             "general": "Added as a general document — its text is now searchable by the assistant.",
             None: "Could not extract readable text from this file, so it was not added."}
    return {"filename": file.filename, "classification": cls, "ingested": bool(kind),
            "kind": kind, "note": notes[kind], **_stats()}


if __name__ == "__main__":
    import uvicorn
    # PORT is provided by cloud hosts (Render/Railway); defaults to 8000 locally
    uvicorn.run(app, host=os.environ.get("HOST", "0.0.0.0"),
                port=int(os.environ.get("PORT", "8000")))

# CORE — Cognitive Operations and Reliability Engine

### Industrial Knowledge Intelligence · Unified Asset & Operations Brain

CORE is a **nine-agent AI platform** that ingests the fragmented document landscape of an
asset-intensive plant — engineering drawings, process flow diagrams, PFMEAs, control
plans, inspection reports, non-conformances, 8D CAPAs and work instructions — and unifies
it into a single queryable knowledge base: an ontological **knowledge graph** combined
with a **RAG vector store**. On top of it, a deterministic consistency auditor detects
cross-document quality gaps the moment data arrives, and an agentic copilot answers
operational questions with **a citation on every claim**.

📄 [Solution Document](pdf/CORE_Solution.pdf) ·
🎬 [Demo Video](https://drive.google.com/file/d/14Wz58dz83FJYXAgA36nVTL8yGFQENiNX/view?usp=sharing)

---

## Key Capabilities

- **The APQP Digital Thread** — drawing → PFD → PFMEA → control plan → inspection →
  NCR → CAPA, stitched automatically into one traceable graph on the shared
  *operation + characteristic* spine.
- **Deterministic Consistency Auditor (C1–C10)** — rule-based, evidence-cited gap
  detection with no LLM in the decision path, including **out-of-spec measurements**
  detected directly from raw inspection readings.
- **Agentic, not assistive** — a tool-calling Copilot Orchestrator autonomously selects
  which specialist agent to invoke (graph traversal, RAG, RCA, QMS) and composes cited
  answers, with conversation memory.
- **Universal ingestion** — recognised industrial documents merge into the knowledge
  graph; any other readable file (reports, spreadsheets, notes) is ingested as a general
  document and becomes searchable, cited by filename.
- **Incremental & live** — the knowledge base boots **empty** and grows as documents are
  uploaded; graph, gap findings, QMS views and the copilot update in real time, and the
  system can be reset to zero at any point.
- **Graceful degradation** — with no API key the platform still runs end-to-end using
  offline lexical retrieval and rule-based agents, suitable for air-gapped environments.
- **Industrial HMI** — a light, shop-floor-legible, mobile-ready interface.

---

## The Nine Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **Ingestion** | accepts documents; two-stage classification (deterministic rules, then LLM only when unsure) |
| 2 | **Extraction** | parses structured entities through deep merged-cell industrial spreadsheet layouts |
| 3 | **Knowledge Graph** | builds and traverses the unified graph; serves per-part sub-graphs |
| 4 | **Retrieval / RAG** | semantic search over every record, with metadata filters and an offline BM25 fallback |
| 5 | **Copilot Orchestrator** | conversational brain; routes questions to specialists via tool-calling; cites every source |
| 6 | **Compliance & Gap Detection** | executes the deterministic C1–C10 checks across the graph |
| 7 | **Maintenance / RCA** | fuses failure history, NCRs, CAPAs and inspection data into root-cause analyses |
| 8 | **Quality / QMS** | manages non-conformances and CAPAs; assembles audit-ready evidence packs |
| 9 | **Lessons Learned** | mines cross-part failure patterns; pushes proactive systemic warnings |

---

## Architecture

```
        Field technician (mobile)          Quality engineer (desktop)
                     \                         /
                      ▼          HTTPS        ▼
        ┌───────────────────────────────────────────────┐
        │  Client Layer — Industrial HMI (Next.js)       │
        │  Overview · Documents (drag-drop) · Graph ·    │
        │  Assistant · Quality (Gaps/QMS/RCA/Lessons)    │
        ├───────────────────────────────────────────────┤
        │  Orchestration — FastAPI                       │
        │  API gateway · Copilot Orchestrator (broker)   │
        ├───────────────────────────────────────────────┤
        │  Agent System (9 agents)                       │
        ├───────────────────────────────────────────────┤
        │  Knowledge Layer                               │
        │  Knowledge Graph · RAG Vector Store ·          │──▶ LLM API
        │  QMS Records · Ingestion Manifest              │    (GPT-4o + embeddings)
        └───────────────────────────────────────────────┘
```

Full architecture and data-flow diagrams are included in the
[solution document](pdf/CORE_Solution.pdf).

---

## Consistency Checks

| ID | Detects | ID | Detects |
|----|---------|----|---------|
| C1 | drawing ↔ control-plan tolerance mismatch | C7 | high-RPN risk watchlist |
| C2 | operation with failure modes but no controls | C8 | systemic root cause spanning operations |
| C3 | unmitigated high-RPN failure (RPN ≥ 90, no action) | C9 | open NCR without a linked CAPA |
| C5 | dangling document reference | C10 | **out-of-spec measurement** (reading vs. tolerance) |
| C6 | broken traceability thread | | |

Example findings from the validation dataset: a casting weight of **97.9 g against a
98–104 g tolerance** flagged automatically from an in-process inspection sheet, and a
single root cause (*coolant concentration out of standard*) driving high-RPN failures
across **five different operations** — invisible to any single-document review.

---

## Validation Dataset

The platform is validated on a multi-part industrial dataset spanning two process
domains — precision steel machining, aluminium high-pressure die casting, and steel
forging + machining — with a full document set per part: PFD, PFMEA, control plan,
inward / in-process / pre-dispatch inspection reports, an NCR/CAR log, an 8D CAPA and a
work instruction (including one in Hindi, demonstrating multilingual retrieval).
Documents are not distributed with this repository; the system ingests them at runtime.

---

## Quick Start

**Requirements:** Python 3.11+ · Node.js 18+ · an OpenAI API key (optional — without it
the platform runs in offline fallback mode).

**Backend**
```bash
pip install -r requirements.txt
# optional: enable full LLM agents
#   create backend/.env containing  OPENAI_API_KEY=sk-...
python -m uvicorn backend.app:app --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev            # http://localhost:3000
```

On Windows, `start.bat` launches both servers with one click.

**Using the app**
1. Open http://localhost:3000 — the knowledge base starts empty.
2. On **Documents**, drag in files. Each is classified and merged live; the graph, gap
   findings, QMS views and the copilot populate as documents arrive.
3. Explore the **Knowledge Graph**, ask the **Assistant**, review **Quality**.
4. Reset to zero anytime with the **RESET** button or `python reset.py`.

---

## Deployment

The deployable artifact is **code only** — no documents ship with it. Every deployment
boots to an empty knowledge base; documents enter at runtime through the UI.

| Option | How |
|---|---|
| **Cloud demo** | Backend → Render via [`render.yaml`](render.yaml) (set `OPENAI_API_KEY` in the dashboard). Frontend → Vercel, root `frontend/`, env `NEXT_PUBLIC_API_BASE=<backend URL>`. |
| **Docker / on-prem** | `docker compose up --build` — backend on `:8000`, uploads and embedding cache persisted via volumes. |
| **Fully local / air-gapped** | `start.bat` with no API key — offline retrieval + rule-based agents, zero external calls. |

---

## Data Privacy & Security

- **Documents never leave the operator's control.** The repository and container images
  contain no plant documents; `data/` is excluded by design. Documents are uploaded at
  runtime and stored only on the backend host.
- **Embeddings are stored on the backend's own disk** (`outputs/emb_cache/`), never in a
  third-party service. The vector store is embedded in-process.
- **Secrets via environment only.** The API key is read from `backend/.env` or the host
  environment and is never committed.
- **Air-gap mode.** With no API key configured, no request ever leaves the machine.

---

## Repository Layout

```
agents/          the nine agents + registry (tool-calling orchestration)
knowledge/       knowledge base builder, incremental catalog, RAG vector store
pipeline/        document parsers (PFD / PFMEA / control plan / drawing)
dataset/         canonical demo-part definitions + document generator
backend/         FastAPI application
frontend/        Next.js industrial HMI
pdf/             solution document
Dockerfile · docker-compose.yml · render.yaml · start.bat · reset.py
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend & agents | Python · FastAPI · 9-agent system · tool-calling orchestration |
| AI & semantics | OpenAI GPT-4o · `text-embedding-3-small` · RAG vector store |
| Extraction | openpyxl · xlrd · pdfplumber · pypdfium2 |
| Frontend | Next.js · TypeScript · Tailwind CSS · react-force-graph |
| State | Embedded NumPy vector store (Qdrant/Pinecone-ready) · persisted ingestion manifest |

---

## Roadmap

- **Computer vision + OCR ballooning** — dedicated balloon-detection + OCR model for
  engineering-drawing digitisation, enabling the C1 tolerance check at enterprise scale.
- **Managed knowledge infrastructure** — Neo4j and Qdrant/Pinecone behind the existing
  interfaces for plant- and enterprise-wide corpora.
- **Regulatory corpus integration** — automatic auditing of live procedures against
  IATF 16949, ISO 9001 and statutory norms.
- **Operational telemetry** — SCADA/IoT operating conditions fused into the RCA agent
  for real-time predictive failure intelligence.

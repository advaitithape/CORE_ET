export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export interface GNode { id: string; type: string; label: string; attrs: any; source: any; part_no?: string; }
export interface GEdge { source: string; target: string; type: string; }
export interface Finding {
  id: string; check: string; severity: "high" | "medium" | "low" | "info";
  part_no: string; title: string; detail: string; evidence: any[]; suggested_fix: string;
}
export interface PartMeta {
  part_no: string; part_name: string; customer: string; supplier: string;
  material: string; process_type: string; operations?: number; failure_modes?: number; open_ncrs?: number;
}
export interface AgentMeta { name: string; title: string; description: string; uses_llm: boolean; }
export interface Doc { name: string; path: string; doc_type: string; part_no: string | null; size_kb: number; source: string; }

async function get<T>(p: string): Promise<T> {
  const r = await fetch(`${API_BASE}${p}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${p} -> ${r.status}`);
  return r.json();
}
async function post<T>(p: string, body: any): Promise<T> {
  const r = await fetch(`${API_BASE}${p}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
}

export const api = {
  system: () => get<any>("/api/system"),
  parts: () => get<{ parts: PartMeta[] }>("/api/parts"),
  graph: (part?: string) => get<{ nodes: GNode[]; edges: GEdge[]; stats?: any }>(`/api/graph${part ? `?part_no=${part}` : ""}`),
  findings: (part?: string) => get<{ findings: Finding[]; summary: any; total: number }>(`/api/findings${part ? `?part_no=${part}` : ""}`),
  qms: (part?: string) => get<any>(`/api/qms${part ? `?part_no=${part}` : ""}`),
  lessons: (explain = false) => get<any>(`/api/lessons${explain ? "?explain=true" : ""}`),
  documents: () => get<{ documents: Doc[] }>("/api/documents"),
  catalog: () => get<{ documents: CatalogDoc[]; ingested_count: number; total: number }>("/api/catalog"),
  ingest: (basename: string) => post<any>("/api/ingest", { basename }),
  reset: () => post<any>("/api/reset", {}),
  chat: (message: string, history: { role: string; content: string }[] = []) =>
    post<any>("/api/chat", { message, history }),
  rca: (part_no: string, op_no: number | null, problem: string) => post<any>("/api/rca", { part_no, op_no, problem }),
  uploadUrl: `${API_BASE}/api/upload`,
};

export interface CatalogDoc { name: string; part_no: string; doc_type: string; ingested: boolean; available: boolean; }

export const NODE_COLORS: Record<string, string> = {
  Part: "#22384c", Operation: "#1f6feb", Control: "#1f8a4c", FailureMode: "#c8302f",
  NCR: "#c9861a", CAPA: "#8a5cf6", Inspection: "#0e8f9e", WorkInstruction: "#6b7a89",
};
export const CHECK_NAMES: Record<string, string> = {
  C1: "Drawing↔Control tolerance", C2: "Uncontrolled operation", C3: "Unmitigated high-RPN",
  C5: "Dangling reference", C6: "Broken thread", C7: "Risk watchlist", C8: "Systemic root cause",
  C9: "NCR without CAPA", C10: "Out-of-spec measurement",
};
export const DOCTYPE_LABEL: Record<string, string> = {
  drawing: "Drawing", pfd: "Process Flow", pfmea: "PFMEA", control_plan: "Control Plan",
  inward_inspection: "Inward Insp.", in_process_ir: "In-Process IR", pdir: "PDIR",
  ncr_car: "NCR / CAR", capa_8d: "8D CAPA", work_instruction: "Work Instruction",
  general: "General Doc", unknown: "Unknown",
};

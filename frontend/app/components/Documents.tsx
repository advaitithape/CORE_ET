"use client";
import { useEffect, useRef, useState } from "react";
import { api, Doc, DOCTYPE_LABEL } from "../lib/api";

export default function Documents({ onChanged }: { onChanged?: () => void }) {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState<any[]>([]);
  const [drag, setDrag] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => api.documents().then((d) => setDocs(d.documents));
  useEffect(() => { load(); }, []);

  async function uploadFiles(files: FileList | File[]) {
    setBusy(true);
    const results: any[] = [];
    for (const f of Array.from(files)) {
      const fd = new FormData(); fd.append("file", f);
      try { const r = await fetch(api.uploadUrl, { method: "POST", body: fd }); results.push(await r.json()); }
      catch (e) { results.push({ filename: (f as File).name, error: String(e) }); }
    }
    setLog(results); await load(); onChanged?.(); setBusy(false);
  }

  async function reset() {
    if (!confirm("Reset the knowledge base to 0 documents?")) return;
    setBusy(true); setLog([]);
    try { await api.reset(); await load(); onChanged?.(); } finally { setBusy(false); }
  }

  const byPart: Record<string, Doc[]> = {};
  docs.forEach((d) => (byPart[d.part_no || "Unassigned"] = byPart[d.part_no || "Unassigned"] || []).push(d));
  const parts = Object.keys(byPart).sort();

  return (
    <div className="fade space-y-4">
      {/* drag-drop upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files); }}
        className={`panel p-8 text-center border-2 border-dashed transition-colors ${drag ? "border-[var(--blue)] bg-[var(--blue-l)]" : "border-[var(--line)]"}`}
      >
        <div className="text-4xl mb-2 text-[var(--blue)]">⤓</div>
        <div className="font-bold text-[var(--steel)] text-lg">Drag &amp; drop documents here</div>
        <div className="muted text-sm mt-1">PFD, PFMEA, Control Plan, inspection reports, NCR, 8D CAPA, work instructions —
          the Ingestion Agent classifies each file and merges it into the knowledge base.</div>
        <div className="mt-4 flex items-center justify-center gap-2">
          <input ref={fileRef} type="file" multiple className="hidden"
            onChange={(e) => e.target.files?.length && uploadFiles(e.target.files)} />
          <button className="hbtn-primary" onClick={() => fileRef.current?.click()} disabled={busy}>
            {busy ? "PROCESSING…" : "⤒ BROWSE FILES"}</button>
          <button className="hbtn" onClick={reset} disabled={busy}
            style={{ borderColor: "var(--red)", color: "var(--red)" }}>⟲ RESET</button>
        </div>
      </div>

      {/* per-file ingestion result */}
      {log.length > 0 && (
        <div className="panel-inset p-3 space-y-1">
          {log.map((r, i) => (
            <div key={i} className="text-[12.5px] mono flex items-center gap-2 flex-wrap">
              <b>{r.filename}</b>
              {r.error ? <span className="sev-high">error</span> : <>
                <span>→ {DOCTYPE_LABEL[r.classification?.doc_type] || r.classification?.doc_type}</span>
                {r.ingested ? <span className="chip bg-info sev-info">ingested ✓</span>
                            : <span className="chip bg-medium sev-medium">classified, not merged</span>}
                <span className="muted">{r.note}</span></>}
            </div>
          ))}
        </div>
      )}

      {/* knowledge-base contents, per part */}
      <div className="panel">
        <div className="px-3 py-2 border-b border-[var(--line)] font-bold text-[var(--steel)] flex items-center gap-2">
          IN THE KNOWLEDGE BASE
          <span className={`chip ${docs.length ? "bg-info sev-info" : "bg-medium sev-medium"}`}>
            <i className="led" style={{ background: docs.length ? "var(--green)" : "var(--amber)" }} />
            {docs.length ? `${docs.length} DOCUMENTS · ${parts.length} PART(S)` : "EMPTY — add documents above"}</span>
        </div>
        {docs.length > 0 && (
          <div className="p-3 space-y-4">
            {parts.map((part) => (
              <div key={part}>
                <div className="text-xs font-bold mono muted mb-1">{part} <span className="text-[var(--muted)]">· {byPart[part].length} docs</span></div>
                <div className="overflow-x-auto">
                  <table className="hgrid">
                    <thead><tr><th>Document</th><th>Classified as</th><th>Source</th><th>Size</th></tr></thead>
                    <tbody>
                      {byPart[part].map((d, i) => (
                        <tr key={i}>
                          <td className="mono text-[12px]">{d.name}</td>
                          <td><span className="chip bg-blue" style={{ color: "var(--blue-d)" }}>{DOCTYPE_LABEL[d.doc_type] || d.doc_type}</span></td>
                          <td><span className={`chip ${d.source === "real" ? "bg-info sev-info" : d.source === "upload" ? "bg-medium sev-medium" : "bg-low sev-low"}`}>{d.source}</span></td>
                          <td className="mono text-xs">{d.size_kb ?? "—"} KB</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

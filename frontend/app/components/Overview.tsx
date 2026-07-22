"use client";
import { useEffect, useState } from "react";
import { api, PartMeta, Finding } from "../lib/api";

export default function Overview({ system, parts, onGoto }:
  { system: any; parts: PartMeta[]; onGoto: (t: string) => void }) {
  const s = system?.stats || {};
  const empty = !parts || parts.length === 0;
  const [findings, setFindings] = useState<Finding[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});

  useEffect(() => {
    api.findings().then((f) => { setFindings(f.findings || []); setSummary(f.summary || {}); });
  }, [system]);

  const openNCR = parts.reduce((a, p) => a + (p.open_ncrs || 0), 0);
  const outOfSpec = findings.filter((f) => f.check === "C10").length;

  return (
    <div className="fade space-y-4">
      {empty && (
        <div className="panel p-5 text-center" style={{ background: "var(--amber-l)", borderColor: "#e6cd93" }}>
          <div className="text-lg font-bold text-[var(--steel)]">CLEAN START — no documents ingested</div>
          <p className="muted mt-1">The knowledge base is empty. Go to <b>Documents</b> and drag in the documents
            you want to ingest — the graph, gaps, QMS and copilot will populate live as you add them.</p>
          <button onClick={() => onGoto("documents")} className="hbtn-primary mt-3">GO TO DOCUMENTS →</button>
        </div>
      )}

      {/* status strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {[
          ["PARTS", s.parts], ["OPERATIONS", s.operations], ["FAILURE MODES", s.failure_modes],
          ["CONTROLS", s.controls], ["NCR / CAPA", `${s.ncrs}/${s.capas}`], ["KB CHUNKS", s.chunks],
        ].map(([l, v]) => (
          <div key={l as string} className="panel p-3">
            <div className="text-2xl font-bold mono">{v}</div>
            <div className="text-[11px] muted font-semibold tracking-wide">{l}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* parts */}
        <div className="panel">
          <div className="px-4 py-2 border-b border-[var(--line)] font-bold text-[var(--steel)]">PARTS IN KNOWLEDGE BASE</div>
          <div className="p-3 space-y-2">
            {parts.map((p) => (
              <button key={p.part_no} onClick={() => onGoto("graph")}
                className="w-full text-left panel-inset p-3 hover:border-[var(--blue)] flex items-center justify-between">
                <div>
                  <div className="font-bold">{p.part_name} <span className="mono text-xs muted">· {p.part_no}</span></div>
                  <div className="text-xs muted">{p.customer} · {p.material} · {p.process_type}</div>
                </div>
                <div className="text-right text-xs mono">
                  <div>{p.operations} ops · {p.failure_modes} FMEA</div>
                  <div className={p.open_ncrs ? "sev-high font-bold" : "muted"}>
                    {p.open_ncrs ? `${p.open_ncrs} OPEN NCR` : "no open NCR"}</div>
                </div>
              </button>
            ))}
            {empty && <div className="muted text-sm p-2">No parts yet — add documents to populate.</div>}
          </div>
        </div>

        {/* compliance & quality snapshot */}
        <div className="panel">
          <div className="px-4 py-2 border-b border-[var(--line)] font-bold text-[var(--steel)] flex items-center gap-2">
            <span>COMPLIANCE &amp; QUALITY SNAPSHOT</span>
            <span className="chip bg-info sev-info ml-auto"><i className="led" style={{ background: "var(--green)" }} />LIVE ON INGEST</span>
          </div>
          <div className="p-3">
            <div className="grid grid-cols-4 gap-2 mb-3">
              <Snap n={summary.high || 0} label="High gaps" sev="high" />
              <Snap n={summary.medium || 0} label="Medium" sev="medium" />
              <Snap n={outOfSpec} label="Out-of-spec" sev="high" />
              <Snap n={openNCR} label="Open NCR" sev={openNCR ? "high" : "info"} />
            </div>
            <div className="text-[11px] font-bold muted mb-1">TOP FINDINGS</div>
            <div className="space-y-1.5">
              {findings.slice(0, 4).map((f) => (
                <div key={f.id} className={`panel-inset p-2 bg-${f.severity}`}>
                  <div className="flex items-start gap-2">
                    <span className={`chip sev-${f.severity} bg-white`}>{f.severity}</span>
                    <span className="mono text-[10px] muted mt-0.5">{f.check}</span>
                    <span className="text-[12.5px] font-semibold flex-1">{f.title}</span>
                  </div>
                </div>
              ))}
              {findings.length === 0 && <div className="muted text-sm">No findings yet — the auditor runs as documents are added.</div>}
            </div>
            {findings.length > 0 && (
              <button onClick={() => onGoto("quality")} className="hbtn-primary mt-3">VIEW ALL IN QUALITY →</button>
            )}
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-4 gap-3">
        {[["DOCUMENTS", "documents", "Add documents + see the corpus"],
          ["KNOWLEDGE GRAPH", "graph", "Trace the digital thread"],
          ["ASSISTANT", "assistant", "Ask the copilot"],
          ["QUALITY", "quality", "Gaps · QMS · RCA · lessons"]].map(([l, t, d]) => (
          <button key={t} onClick={() => onGoto(t)} className="panel p-4 text-left hover:border-[var(--blue)]">
            <div className="font-bold text-[var(--steel)]">{l}</div>
            <div className="text-xs muted mt-1">{d}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function Snap({ n, label, sev }: { n: number; label: string; sev: string }) {
  return (
    <div className={`rounded p-2 border bg-${sev} text-center`}>
      <div className={`text-xl font-bold sev-${sev}`}>{n}</div>
      <div className="text-[10px] muted">{label}</div>
    </div>
  );
}

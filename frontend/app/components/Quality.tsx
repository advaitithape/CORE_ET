"use client";
import { useEffect, useState } from "react";
import { api, Finding, CHECK_NAMES, PartMeta } from "../lib/api";

const SUB = ["Gaps", "QMS", "Lessons", "RCA"];

export default function Quality({ parts }: { parts: PartMeta[] }) {
  const [sub, setSub] = useState("Gaps");
  return (
    <div className="fade h-full flex flex-col">
      <div className="flex gap-1 mb-3">
        {SUB.map((s) => (
          <button key={s} onClick={() => setSub(s)} className={`hbtn ${sub === s ? "!border-[var(--blue)] !text-[var(--blue-d)]" : ""}`}>{s.toUpperCase()}</button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto">
        {sub === "Gaps" && <Gaps />}
        {sub === "QMS" && <QMS />}
        {sub === "Lessons" && <Lessons />}
        {sub === "RCA" && <RCA parts={parts} />}
      </div>
    </div>
  );
}

function Gaps() {
  const [d, setD] = useState<any>(null);
  const [open, setOpen] = useState<string | null>(null);
  useEffect(() => { api.findings().then(setD); }, []);
  if (!d) return <div className="muted">Running auditor…</div>;
  return (
    <div className="space-y-2">
      <div className="flex gap-2 mb-1">
        {Object.entries(d.summary).map(([k, v]: any) => (
          <span key={k} className={`chip bg-${k} sev-${k}`}>{k}: {v}</span>
        ))}
        <span className="chip">{d.total} TOTAL</span>
      </div>
      {d.findings.map((f: Finding) => (
        <div key={f.id} className={`panel bg-${f.severity} p-3`}>
          <div className="flex items-start gap-2 cursor-pointer" onClick={() => setOpen(open === f.id ? null : f.id)}>
            <span className={`chip sev-${f.severity} bg-white`}>{f.severity}</span>
            <span className="mono text-[11px] muted mt-0.5">{f.check}</span>
            <span className="font-semibold text-[13.5px] flex-1">{f.title}</span>
            <span className="muted">{open === f.id ? "−" : "+"}</span>
          </div>
          {open === f.id && (
            <div className="mt-2 space-y-2 fade">
              <p className="text-[13px]">{f.detail}</p>
              <div className="flex flex-wrap gap-1">
                {f.evidence.map((e, i) => (
                  <span key={i} className="mono text-[11px] panel-inset px-2 py-0.5">
                    {e.doc}{e.op != null ? ` · Op ${e.op}` : ""}{e.note ? ` · ${e.note}` : ""}</span>
                ))}
              </div>
              <div className="text-[13px]"><b className="text-[var(--blue-d)]">Fix: </b>{f.suggested_fix}</div>
              <div className="text-[11px] mono muted">check: {CHECK_NAMES[f.check]}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function QMS() {
  const [d, setD] = useState<any>(null);
  useEffect(() => { api.qms().then(setD); }, []);
  if (!d) return <div className="muted">Loading QMS…</div>;
  return (
    <div className="space-y-3">
      {d.parts.map((p: any) => (
        <div key={p.part_no} className="panel">
          <div className="px-3 py-2 border-b border-[var(--line)] font-bold text-[var(--steel)]">
            {p.part_name} <span className="mono text-xs muted">· {p.part_no}</span>
            <span className="ml-2 chip">{p.inspections.length} INSPECTIONS ON FILE</span>
            {p.open_ncrs.length > 0 && <span className="ml-1 chip bg-high sev-high">{p.open_ncrs.length} OPEN NCR</span>}
          </div>
          <div className="p-3 grid md:grid-cols-2 gap-3">
            <div>
              <div className="text-xs font-bold muted mb-1">NON-CONFORMANCES</div>
              {(p.ncrs || []).map((n: any, i: number) => (
                <div key={i} className="panel-inset p-2 mb-1 text-[12.5px]">
                  <div className="flex justify-between"><b>{n.reason}</b>
                    <span className={`chip ${n.status === "Open" ? "bg-high sev-high" : "bg-info sev-info"}`}>{n.status}</span></div>
                  <div className="muted">Rej {n.rej_pct}% · in-proc {n.inprocess_rej}, PDI {n.pdi_rej} → {n.corrective_action}</div>
                </div>
              ))}
            </div>
            <div>
              <div className="text-xs font-bold muted mb-1">8D CAPA</div>
              {(p.capas || []).map((c: any, i: number) => (
                <div key={i} className="panel-inset p-2 mb-1 text-[12.5px]">
                  <div className="flex justify-between"><b className="mono">{c.notification_no}</b>
                    <span className="chip bg-medium sev-medium">{c.status}</span></div>
                  <div className="muted"><b>Root cause:</b> {c.root_cause}</div>
                  <div className="muted"><b>CA:</b> {c.corrective_action}</div>
                </div>
              ))}
              {(!p.capas || p.capas.length === 0) && <div className="text-xs muted">none</div>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function Lessons() {
  const [d, setD] = useState<any>(null);
  useEffect(() => { api.lessons(true).then(setD); }, []);
  if (!d) return <div className="muted">Mining cross-part patterns…</div>;
  return (
    <div className="space-y-3">
      {d.narrative && (
        <div className="panel p-3">
          <div className="font-bold text-[var(--steel)] mb-1">FAILURE INTELLIGENCE — CROSS-PART SUMMARY</div>
          <div className="text-[13.5px] whitespace-pre-wrap">{d.narrative}</div>
        </div>
      )}
      <div className="panel">
        <div className="px-3 py-2 border-b border-[var(--line)] font-bold text-[var(--steel)]">RECURRING THEMES</div>
        <div className="p-3 space-y-2">
          {d.patterns.map((p: any, i: number) => (
            <div key={i} className="panel-inset p-2">
              <div className="flex items-center gap-2">
                <b className="capitalize">{p.theme}</b>
                <span className="chip">{p.count} records</span>
                {p.parts.map((pt: string) => <span key={pt} className="chip bg-blue mono" style={{ color: "var(--blue-d)" }}>{pt}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function RCA({ parts }: { parts: PartMeta[] }) {
  const [part, setPart] = useState(parts[0]?.part_no || "");
  const [op, setOp] = useState("");
  const [problem, setProblem] = useState("");
  const [res, setRes] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  async function run() {
    setBusy(true); setRes(null);
    try { setRes(await api.rca(part, op ? parseInt(op) : null, problem)); }
    finally { setBusy(false); }
  }
  return (
    <div className="space-y-3">
      <div className="panel p-3 flex gap-2 flex-wrap items-end">
        <label className="text-xs muted">Part
          <select value={part} onChange={(e) => setPart(e.target.value)} className="block panel-inset px-2 py-1.5 mt-0.5">
            {parts.map((p) => <option key={p.part_no}>{p.part_no}</option>)}</select></label>
        <label className="text-xs muted">Operation (opt)
          <input value={op} onChange={(e) => setOp(e.target.value)} className="block panel-inset px-2 py-1.5 mt-0.5 w-24" placeholder="e.g. 20" /></label>
        <label className="text-xs muted flex-1">Problem (opt)
          <input value={problem} onChange={(e) => setProblem(e.target.value)} className="block panel-inset px-2 py-1.5 mt-0.5 w-full" placeholder="describe the issue" /></label>
        <button className="hbtn-primary" onClick={run} disabled={busy}>{busy ? "ANALYSING…" : "RUN RCA"}</button>
      </div>
      {res && (
        <div className="panel p-3 fade">
          <div className="font-bold text-[var(--steel)] mb-1">ROOT-CAUSE ANALYSIS <span className="chip bg-info sev-info ml-1">{res.mode}</span></div>
          {res.analysis
            ? <div className="text-[13.5px] whitespace-pre-wrap">{res.analysis}</div>
            : <div className="text-[13px]">Likely root cause: <b>{res.root_cause}</b></div>}
        </div>
      )}
    </div>
  );
}

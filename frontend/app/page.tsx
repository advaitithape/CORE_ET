"use client";
import { useEffect, useState } from "react";
import { api, PartMeta } from "./lib/api";
import Overview from "./components/Overview";
import Documents from "./components/Documents";
import GraphView from "./components/GraphView";
import Assistant from "./components/Assistant";
import Quality from "./components/Quality";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "documents", label: "Documents" },
  { id: "graph", label: "Knowledge Graph" },
  { id: "assistant", label: "Assistant" },
  { id: "quality", label: "Quality" },
];

export default function Home() {
  const [tab, setTab] = useState("overview");
  const [system, setSystem] = useState<any>(null);
  const [parts, setParts] = useState<PartMeta[]>([]);
  const [err, setErr] = useState<string | null>(null);

  function reload() {
    Promise.all([api.system(), api.parts()])
      .then(([s, p]) => { setSystem(s); setParts(p.parts); setErr(null); })
      .catch((e) => setErr(String(e)));
  }
  useEffect(() => { reload(); }, []);

  return (
    <main className="h-screen flex flex-col">
      {/* HMI title bar */}
      <header className="bg-[var(--steel)] text-white shrink-0">
        <div className="px-3 sm:px-4 py-2 flex items-center gap-2 sm:gap-3">
          <div className="w-7 h-7 shrink-0 border-2 border-white/70 flex items-center justify-center font-black text-sm">C</div>
          <div className="min-w-0">
            <div className="font-bold leading-tight tracking-wide text-[13px] sm:text-base truncate">CORE</div>
            <div className="hidden sm:block text-[11px] text-white/70 leading-tight">Cognitive Operations &amp; Reliability Engine · Unified Asset &amp; Operations Brain</div>
          </div>
          <div className="ml-auto flex items-center gap-2 sm:gap-3 text-[10px] sm:text-[11px] shrink-0">
            <span className="flex items-center gap-1"><i className="led" style={{ background: system?.llm_key ? "#37d67a" : "#c9861a" }} />
              <span className="hidden sm:inline">{system ? (system.llm_key ? "LLM ONLINE" : "FALLBACK") : "…"}</span></span>
            <span className="flex items-center gap-1"><i className="led" style={{ background: err ? "#c8302f" : "#37d67a" }} />
              {err ? "OFFLINE" : "OK"}</span>
          </div>
        </div>
        <nav className="flex border-t border-[#33485c] overflow-x-auto whitespace-nowrap no-scrollbar">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`tab shrink-0 ${tab === t.id ? "tab-active" : ""}`}>{t.label}</button>
          ))}
        </nav>
      </header>

      <section className="flex-1 min-h-0 p-3 sm:p-4">
        {err && <div className="panel bg-high p-4 text-sm">Backend offline on <span className="mono">:8000</span>.
          Start it: <span className="mono">python -m uvicorn backend.app:app --port 8000</span> ({err})</div>}
        {!system && !err && <div className="muted">Booting knowledge base &amp; agents…</div>}
        {system && (
          <div className="h-full overflow-y-auto">
            {tab === "overview" && <Overview system={system} parts={parts} onGoto={setTab} />}
            {tab === "documents" && <Documents onChanged={reload} />}
            {tab === "graph" && <div className="h-full"><GraphView parts={parts} /></div>}
            {tab === "assistant" && <div className="h-full"><Assistant /></div>}
            {tab === "quality" && <Quality parts={parts} />}
          </div>
        )}
      </section>
    </main>
  );
}

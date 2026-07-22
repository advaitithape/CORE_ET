"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

interface Msg { role: "user" | "assistant"; text: string; mode?: string; tools?: any[]; }
const STORE_KEY = "iki_chat_session";

const SUGGEST = [
  "Why are we getting leaks on the Base part and what's the root cause?",
  "Which parts have out-of-spec measurements, and are any NCRs still open?",
  "Is there a systemic root cause affecting multiple operations on the Pinion Shaft?",
  "What does the work instruction for the die casting operation say?",
];

export default function Assistant() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);

  // load this session's chat (survives tab switches / reloads; cleared when the tab closes)
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(STORE_KEY);
      if (saved) setMsgs(JSON.parse(saved));
    } catch { /* ignore */ }
  }, []);
  useEffect(() => {
    try { sessionStorage.setItem(STORE_KEY, JSON.stringify(msgs)); } catch { /* ignore */ }
    end.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  async function send(q: string) {
    if (!q.trim() || busy) return;
    const history = msgs.map((m) => ({ role: m.role, content: m.text }));
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setInput(""); setBusy(true);
    try {
      const r = await api.chat(q, history);
      setMsgs((m) => [...m, { role: "assistant", text: r.answer, mode: r.mode, tools: r.tools_used }]);
    } catch { setMsgs((m) => [...m, { role: "assistant", text: "Backend unreachable on :8000." }]); }
    finally { setBusy(false); }
  }

  function clearChat() {
    setMsgs([]);
    try { sessionStorage.removeItem(STORE_KEY); } catch { /* ignore */ }
  }

  return (
    <div className="panel h-full flex flex-col fade">
      <div className="px-4 py-2 border-b border-[var(--line)] font-bold text-[var(--steel)] flex items-center gap-2">
        KNOWLEDGE COPILOT
        <span className="chip bg-info sev-info"><i className="led" style={{ background: "var(--green)" }} />AGENTIC · TOOL-CALLING</span>
        {msgs.length > 0 && <button onClick={clearChat} className="hbtn text-xs ml-auto">CLEAR CHAT</button>}
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {msgs.length === 0 && (
          <div className="max-w-2xl">
            <p className="muted text-[13px] mb-3">Ask across all parts and document types. The orchestrator
              routes your question to the specialist agents (RAG search, graph, compliance, RCA, QMS) and
              answers with citations. The assistant remembers this conversation until you close the tab.</p>
            <div className="grid sm:grid-cols-2 gap-2">
              {SUGGEST.map((s) => (
                <button key={s} onClick={() => send(s)} className="panel-inset p-2.5 text-left text-[13px] hover:border-[var(--blue)]">{s}</button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} fade`}>
            <div className={`max-w-[82%] px-3.5 py-2.5 text-[14px] leading-relaxed whitespace-pre-wrap rounded
              ${m.role === "user" ? "bg-[var(--blue-l)] border border-[#a9cbf5]" : "panel-inset"}`}>
              {cite(m.text)}
              {m.tools && m.tools.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {m.tools.map((t: any, k: number) => (
                    <span key={k} className="chip bg-blue mono" style={{ color: "var(--blue-d)" }}>⚙ {t.tool}</span>
                  ))}
                </div>
              )}
              {m.mode === "fallback" && <div className="text-[10px] mono muted mt-1">grounded fallback</div>}
            </div>
          </div>
        ))}
        {busy && <div className="muted text-sm fade">⚙ agents working…</div>}
        <div ref={end} />
      </div>
      <div className="border-t border-[var(--line)] p-3 flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder="Ask about any part, failure, control, NCR, CAPA…"
          className="flex-1 panel-inset px-3 py-2.5 text-sm outline-none focus:border-[var(--blue)]" />
        <button className="hbtn-primary" onClick={() => send(input)} disabled={busy}>SEND</button>
      </div>
    </div>
  );
}

function cite(text: string) {
  return text.split(/(\[[^\]]+\])/g).map((p, i) =>
    /^\[.+\]$/.test(p)
      ? <span key={i} className="mono text-[11px] px-1.5 py-0.5 mx-0.5 rounded bg-[var(--blue-l)] text-[var(--blue-d)] border border-[#a9cbf5]">{p.slice(1, -1)}</span>
      : <span key={i}>{p}</span>);
}

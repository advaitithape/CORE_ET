"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { api, GNode, NODE_COLORS, PartMeta } from "../lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export default function GraphView({ parts }: { parts: PartMeta[] }) {
  const [part, setPart] = useState<string>(parts[0]?.part_no || "CE21609");
  const [data, setData] = useState<{ nodes: GNode[]; edges: any[] }>({ nodes: [], edges: [] });
  const [sel, setSel] = useState<GNode | null>(null);
  const [dims, setDims] = useState({ w: 800, h: 560 });
  const fg = useRef<any>(null);
  const wrap = useRef<HTMLDivElement>(null);

  useEffect(() => { api.graph(part).then((g) => { setData({ nodes: g.nodes, edges: g.edges }); setSel(null); }); }, [part]);
  useEffect(() => {
    const el = wrap.current; if (!el) return;
    const ro = new ResizeObserver(() => setDims({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el); return () => ro.disconnect();
  }, []);

  const gdata = useMemo(() => ({
    nodes: data.nodes.map((n) => ({ ...n })),
    links: data.edges.map((e) => ({ ...e })),
  }), [data]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    data.nodes.forEach((n) => (c[n.type] = (c[n.type] || 0) + 1));
    return c;
  }, [data]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-3 h-full fade">
      <div className="panel relative overflow-hidden h-[55vh] min-h-[320px] lg:h-auto" ref={wrap}>
        <div className="absolute top-2 left-2 z-10 flex gap-1 items-center flex-wrap">
          {parts.map((p) => (
            <button key={p.part_no} onClick={() => setPart(p.part_no)}
              className={`hbtn text-xs ${part === p.part_no ? "!border-[var(--blue)] !text-[var(--blue-d)]" : ""}`}>
              {p.part_no}</button>
          ))}
          <button className="hbtn text-xs" onClick={() => fg.current?.zoomToFit(400, 50)}>FIT</button>
        </div>
        <div className="absolute bottom-2 left-2 z-10 flex gap-2 flex-wrap text-[11px]">
          {Object.entries(NODE_COLORS).filter(([k]) => counts[k]).map(([k, c]) => (
            <span key={k} className="chip bg-white" style={{ background: "#fff" }}>
              <i className="led" style={{ background: c }} />{k} {counts[k]}</span>
          ))}
        </div>
        <ForceGraph2D ref={fg} graphData={gdata} width={dims.w} height={dims.h}
          backgroundColor="#f7f9fb" nodeRelSize={5}
          linkColor={() => "#c2ccd6"} linkWidth={0.7} cooldownTicks={110}
          onEngineStop={() => fg.current?.zoomToFit(400, 50)}
          nodeVal={(n: any) => n.type === "Part" ? 16 : n.type === "Operation" ? 8
            : n.type === "FailureMode" ? Math.max(2, (n.attrs?.rpn || 20) / 20) : 4}
          nodeColor={(n: any) => NODE_COLORS[n.type] || "#888"}
          nodeLabel={(n: any) => `<div style="font:12px sans-serif;color:#1b2733;background:#fff;padding:4px 6px;border:1px solid #b7c2cd;border-radius:3px">
            <b>${n.type}</b><br/>${(n.label || "").replace(/</g, "")}${n.attrs?.rpn ? `<br/>RPN ${n.attrs.rpn}` : ""}</div>`}
          onNodeClick={(n: any) => { setSel(n); fg.current?.centerAt(n.x, n.y, 400); fg.current?.zoom(2.4, 400); }} />
      </div>

      <div className="panel p-3 overflow-y-auto max-h-[34vh] lg:max-h-none">
        {!sel ? (
          <div className="text-sm">
            <div className="font-bold text-[var(--steel)] mb-2">DIGITAL THREAD · {part}</div>
            <p className="muted text-[13px]">Every node is stitched from a source document and carries a citation.
              Click any node to inspect its evidence. Colours: operations, controls, failure modes,
              NCRs, CAPAs and inspections are all linked on the shared operation spine.</p>
          </div>
        ) : (
          <div className="fade">
            <div className="flex items-center gap-2 mb-1">
              <i className="led" style={{ background: NODE_COLORS[sel.type] }} />
              <span className="mono text-[11px] muted uppercase">{sel.type}</span>
            </div>
            <div className="font-bold mb-2 leading-snug">{sel.label}</div>
            <div className="space-y-1.5">
              {Object.entries(sel.attrs || {}).filter(([, v]) => v !== null && v !== "" && v !== undefined)
                .map(([k, v]) => (
                  <div key={k} className="panel-inset p-1.5">
                    <div className="text-[10px] mono muted uppercase">{k}</div>
                    <div className="text-[13px] whitespace-pre-wrap">{Array.isArray(v) ? (v as any[]).join("; ") : String(v)}</div>
                  </div>
                ))}
            </div>
            <div className="text-[10px] mono muted mt-2">source: {sel.source?.doc}{sel.source?.op != null ? ` · Op ${sel.source.op}` : ""}</div>
            <button className="hbtn text-xs mt-3" onClick={() => setSel(null)}>← BACK</button>
          </div>
        )}
      </div>
    </div>
  );
}

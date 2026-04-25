import { useEffect, useRef } from "react";
import type { AgentLogEntry } from "../types";

type Props = { entries: AgentLogEntry[] };

const TYPE_TONE: Record<AgentLogEntry["type"], string> = {
  started: "border-sky-400/20 bg-sky-400/10 text-sky-100",
  text: "border-white/10 bg-white/[0.04] text-white/85",
  tool_use: "border-amber-300/20 bg-amber-300/10 text-amber-100",
  tool_result: "border-emerald-300/20 bg-emerald-300/10 text-emerald-100",
  completed: "border-emerald-400/30 bg-emerald-400/15 text-emerald-100",
  failed: "border-rose-400/30 bg-rose-400/15 text-rose-100",
};

const TYPE_LABEL: Record<AgentLogEntry["type"], string> = {
  started: "started",
  text: "text",
  tool_use: "tool",
  tool_result: "result",
  completed: "completed",
  failed: "failed",
};

export function AgentLogPanel({ entries }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [entries.length]);

  if (entries.length === 0) {
    return (
      <p className="text-sm text-white/45">
        No activity yet. Run this branch to start an agent session.
      </p>
    );
  }

  return (
    <div ref={ref} className="max-h-[340px] space-y-2 overflow-y-auto pr-1">
      {entries.map((e) => (
        <LogRow key={e.id} entry={e} />
      ))}
    </div>
  );
}

function LogRow({ entry }: { entry: AgentLogEntry }) {
  const tone = TYPE_TONE[entry.type];
  return (
    <div className={`rounded-xl border px-3 py-2 ${tone}`}>
      <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.18em] opacity-70">
        <span>{TYPE_LABEL[entry.type]}</span>
        <span>{new Date(entry.timestamp).toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" })}</span>
      </div>
      {entry.tool_name ? (
        <p className="mt-1 font-mono text-[12px] leading-5 text-white/80">
          {entry.tool_name}
          {entry.tool_input ? <span className="text-white/50"> {JSON.stringify(entry.tool_input).slice(0, 140)}</span> : null}
        </p>
      ) : null}
      {entry.content ? (
        <p className="mt-1 whitespace-pre-wrap font-mono text-[12px] leading-5">
          {entry.content}
        </p>
      ) : null}
    </div>
  );
}

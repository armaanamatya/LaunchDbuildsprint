import { useEffect, useRef } from "react";
import type { AgentLogEntry } from "../types";

type Props = { entries: AgentLogEntry[] };

const TYPE_TONE: Record<AgentLogEntry["type"], { stripe: string; tag: string }> = {
  started:     { stripe: "bg-accent",                                 tag: "text-accent" },
  text:        { stripe: "bg-line-strong",                            tag: "text-ink-muted" },
  tool_use:    { stripe: "bg-[color:var(--strategy-route-local)]",    tag: "text-[color:var(--strategy-route-local)]" },
  tool_result: { stripe: "bg-[color:var(--color-success)]",           tag: "text-[color:var(--color-success)]" },
  completed:   { stripe: "bg-[color:var(--color-success)]",           tag: "text-[color:var(--color-success)]" },
  failed:      { stripe: "bg-danger",                                 tag: "text-danger" },
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
      <p className="font-mono text-[12px] text-ink-soft">
        No activity yet. Run this branch to start an agent session.
      </p>
    );
  }

  return (
    <div ref={ref} className="max-h-[360px] space-y-1.5 overflow-y-auto pr-1">
      {entries.map((e) => (
        <LogRow key={e.id} entry={e} />
      ))}
    </div>
  );
}

function LogRow({ entry }: { entry: AgentLogEntry }) {
  const tone = TYPE_TONE[entry.type];
  const time = new Date(entry.timestamp).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div className="relative rounded-sm border border-line bg-surface pl-3 pr-3 py-2">
      <span className={`pointer-events-none absolute inset-y-1.5 left-0 w-[3px] rounded-r-sm ${tone.stripe}`} />
      <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-eyebrow">
        <span className={tone.tag}>{TYPE_LABEL[entry.type]}</span>
        <span className="tabular-num text-ink-soft">{time}</span>
      </div>
      {entry.tool_name ? (
        <p className="mt-1 font-mono text-[12px] leading-5 text-ink">
          <span className="text-ink-muted">›</span> {entry.tool_name}
          {entry.tool_input ? (
            <span className="text-ink-muted"> {JSON.stringify(entry.tool_input).slice(0, 140)}</span>
          ) : null}
        </p>
      ) : null}
      {entry.content ? (
        <p className="mt-1 whitespace-pre-wrap text-[12.5px] leading-5 text-ink">
          {entry.content}
        </p>
      ) : null}
    </div>
  );
}

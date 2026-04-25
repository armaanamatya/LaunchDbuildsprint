import { useGraphStore } from "../store/graphStore";

const STYLES = {
  connecting: { dot: "bg-amber-300 animate-pulse", label: "Connecting" },
  open:       { dot: "bg-emerald-400 shadow-[0_0_18px_rgba(74,222,128,0.65)]", label: "Live" },
  reconnecting: { dot: "bg-amber-300 animate-pulse", label: "Reconnecting" },
  closed:     { dot: "bg-rose-400", label: "Offline" },
} as const;

export function ConnectionIndicator() {
  const status = useGraphStore((s) => s.connection);
  const s = STYLES[status];
  return (
    <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-white/10 bg-black/35 px-3 py-2 text-[11px] font-medium text-white/70 backdrop-blur-xl">
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </div>
  );
}

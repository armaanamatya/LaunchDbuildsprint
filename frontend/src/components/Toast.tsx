import { useGraphStore } from "../store/graphStore";

const KIND_TONE = {
  info: "border-white/10 bg-[#0d0f11] text-white/85",
  success: "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
  error: "border-rose-400/30 bg-rose-400/10 text-rose-100",
} as const;

export function ToastHost() {
  const toasts = useGraphStore((s) => s.toasts);
  const dismiss = useGraphStore((s) => s.dismissToast);
  return (
    <div className="pointer-events-none fixed bottom-6 left-6 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto max-w-sm rounded-xl border px-4 py-3 text-sm shadow-[0_18px_50px_rgba(0,0,0,0.5)] ${KIND_TONE[t.kind]}`}
          onClick={() => dismiss(t.id)}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}

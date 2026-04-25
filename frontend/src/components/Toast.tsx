import { useGraphStore } from "../store/graphStore";

const KIND_TONE = {
  info:    "border-line bg-surface text-ink",
  success: "border-[color:var(--color-success)]/30 bg-success-soft text-success",
  error:   "border-[color:var(--color-danger)]/30 bg-danger-soft text-danger",
} as const;

export function ToastHost() {
  const toasts = useGraphStore((s) => s.toasts);
  const dismiss = useGraphStore((s) => s.dismissToast);
  return (
    <div className="pointer-events-none fixed bottom-6 left-6 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto max-w-sm cursor-pointer rounded-md border px-4 py-3 text-sm shadow-panel-lg ${KIND_TONE[t.kind]}`}
          onClick={() => dismiss(t.id)}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}

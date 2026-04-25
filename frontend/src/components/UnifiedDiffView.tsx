type Props = { diff: string };

function lineClass(line: string): string {
  if (line.startsWith("+++") || line.startsWith("---")) return "text-white/45";
  if (line.startsWith("@@")) return "text-sky-300";
  if (line.startsWith("+")) return "bg-emerald-400/10 text-emerald-100";
  if (line.startsWith("-")) return "bg-rose-400/10 text-rose-100";
  if (line.startsWith("diff ") || line.startsWith("index ")) return "text-white/35";
  return "text-white/72";
}

export function UnifiedDiffView({ diff }: Props) {
  const lines = diff.split("\n");
  return (
    <pre className="overflow-auto rounded-2xl border border-white/8 bg-black/55 p-3 text-[12px] leading-5">
      {lines.map((line, i) => (
        <div key={i} className={`whitespace-pre px-2 ${lineClass(line)}`}>
          {line || " "}
        </div>
      ))}
    </pre>
  );
}

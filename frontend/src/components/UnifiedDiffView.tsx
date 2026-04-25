type Props = { diff: string };

interface DiffLine {
  text: string;
  kind: "header" | "hunk" | "add" | "remove" | "context" | "meta";
  oldNum: number | null;
  newNum: number | null;
}

const HUNK_RE = /^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@/;

function parseDiff(diff: string): DiffLine[] {
  const out: DiffLine[] = [];
  let oldLine = 0;
  let newLine = 0;
  for (const text of diff.split("\n")) {
    if (text.startsWith("diff --git ") || text.startsWith("index ")) {
      out.push({ text, kind: "meta", oldNum: null, newNum: null });
      continue;
    }
    if (text.startsWith("+++") || text.startsWith("---")) {
      out.push({ text, kind: "header", oldNum: null, newNum: null });
      continue;
    }
    const hunk = HUNK_RE.exec(text);
    if (hunk) {
      oldLine = Number(hunk[1]);
      newLine = Number(hunk[3]);
      out.push({ text, kind: "hunk", oldNum: null, newNum: null });
      continue;
    }
    if (text.startsWith("+")) {
      out.push({ text, kind: "add", oldNum: null, newNum: newLine++ });
      continue;
    }
    if (text.startsWith("-")) {
      out.push({ text, kind: "remove", oldNum: oldLine++, newNum: null });
      continue;
    }
    out.push({ text, kind: "context", oldNum: oldLine++, newNum: newLine++ });
  }
  return out;
}

const KIND_ROW: Record<DiffLine["kind"], string> = {
  meta:    "bg-paper-deep text-ink-soft",
  header:  "bg-paper-deep text-ink-soft",
  hunk:    "bg-paper-deep text-ink-muted font-medium",
  add:     "bg-[color:var(--color-success-soft)] text-ink",
  remove:  "bg-[color:var(--color-danger-soft)] text-ink",
  context: "text-ink",
};

export function UnifiedDiffView({ diff }: Props) {
  const lines = parseDiff(diff);

  return (
    <pre className="overflow-auto rounded-sm border border-line bg-surface font-mono text-[11.5px] leading-5">
      <table className="min-w-full">
        <tbody>
          {lines.map((line, i) => (
            <tr key={i} className={KIND_ROW[line.kind]}>
              <td className="select-none whitespace-pre px-2 py-px text-right tabular-num text-ink-soft">
                {line.oldNum ?? ""}
              </td>
              <td className="select-none whitespace-pre px-2 py-px text-right tabular-num text-ink-soft">
                {line.newNum ?? ""}
              </td>
              <td className="w-full whitespace-pre py-px pl-2 pr-3">
                {line.text || " "}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </pre>
  );
}

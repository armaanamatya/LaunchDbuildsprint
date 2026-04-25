import { Link } from "react-router-dom";

export function Landing() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <TopNav />
      <main>
        <Hero />
        <Manifesto />
        <HowItWorks />
        <Preview />
        <BuiltWith />
        <ClosingCTA />
      </main>
      <Footer />
    </div>
  );
}

function TopNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper/85 backdrop-blur">
      <div className="mx-auto flex max-w-[1180px] items-center justify-between px-6 py-4 sm:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <BrandMark />
          <span className="font-display text-[15px] font-semibold tracking-[-0.01em] text-ink">
            Agent Graph
          </span>
        </Link>
        <nav className="flex items-center gap-2">
          <Link
            to="/app"
            className="rounded-sm px-3 py-1.5 text-[12.5px] font-medium text-ink-muted hover:text-ink"
          >
            Sign in
          </Link>
          <Link
            to="/app"
            className="inline-flex items-center gap-1.5 rounded-sm bg-accent px-4 py-2 text-[12.5px] font-semibold text-paper-deep shadow-panel transition-colors hover:bg-accent-strong"
          >
            Get started <span aria-hidden>→</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_70%_28%,rgba(216,73,46,0.07),transparent_60%)]" />
      <div className="relative mx-auto grid max-w-[1180px] grid-cols-1 gap-8 px-6 pb-24 pt-20 sm:px-8 sm:pt-28 lg:grid-cols-[minmax(0,1fr)_440px] lg:gap-12 lg:pb-32 lg:pt-32">
        <div className="max-w-[640px]">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-ink-muted">
            Agent Graph · A branching workspace for software decisions
          </p>
          <h1 className="mt-6 font-display text-[3.2rem] font-semibold leading-[0.98] tracking-[-0.035em] text-ink sm:text-[4.2rem] lg:text-[5rem]">
            One prompt.
            <br />
            Three implementations.
            <br />
            <em className="font-semibold not-italic text-accent">One winner.</em>
          </h1>
          <p className="mt-7 max-w-[540px] text-[15.5px] leading-[1.65] text-ink-muted sm:text-[16.5px]">
            Spawn three Claude agents on the same task. Each works in an
            isolated git worktree with a different architectural strategy.
            Compare the diffs side by side. Merge the winner with one click.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link
              to="/app"
              className="inline-flex items-center gap-2 rounded-sm bg-accent px-6 py-3.5 text-[14px] font-semibold text-paper-deep shadow-panel transition-colors hover:bg-accent-strong"
            >
              Open the workspace <span aria-hidden>→</span>
            </Link>
            <Link
              to="/app"
              className="inline-flex items-center gap-2 rounded-sm border border-line-strong bg-surface px-6 py-3.5 text-[14px] font-semibold text-ink transition-colors hover:bg-paper-deep"
            >
              Sign in
            </Link>
          </div>
          <p className="mt-6 font-mono text-[11px] uppercase tracking-eyebrow text-ink-soft">
            ⌘ N to spawn · No signup required for the demo
          </p>
        </div>

        <div className="relative hidden lg:flex lg:items-center lg:justify-center">
          <BranchMotif />
        </div>
      </div>
    </section>
  );
}

function Manifesto() {
  return (
    <section className="border-y border-line bg-surface">
      <div className="mx-auto max-w-[1180px] px-6 py-24 sm:px-8 sm:py-28">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-ink-muted">
          The thesis
        </p>
        <blockquote className="mt-6 max-w-[940px] font-display text-[2rem] font-medium leading-[1.18] tracking-[-0.02em] text-ink sm:text-[2.6rem]">
          Code quality is becoming commoditized.{" "}
          <span className="text-ink-muted">
            The moat is idea, design, and decision-making.
          </span>{" "}
          Real software is not one linear chat —{" "}
          <em className="not-italic text-accent">it branches.</em>
        </blockquote>
        <p className="mt-8 font-mono text-[11px] uppercase tracking-eyebrow text-ink-soft">
          — Agent Graph thesis
        </p>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      n: "01",
      title: "Spawn",
      body: "Write one prompt. Three Claude agents fork into three isolated git worktrees, each with a different strategy: route-local, dependency, middleware.",
      diagram: <SpawnDiagram />,
    },
    {
      n: "02",
      title: "Compare",
      body: "Watch them work in real time on the graph. Open the diff panel and review every change side by side as agents stream their progress.",
      diagram: <CompareDiagram />,
    },
    {
      n: "03",
      title: "Merge",
      body: "Pick the winner. One click merges into main with conflict detection and a clean git history. The losing branches stay archived in case you change your mind.",
      diagram: <MergeDiagram />,
    },
  ];

  return (
    <section className="mx-auto max-w-[1180px] px-6 py-24 sm:px-8 sm:py-28">
      <div className="mb-14 max-w-[720px]">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-ink-muted">
          How it works
        </p>
        <h2 className="mt-4 font-display text-[2rem] font-semibold leading-[1.05] tracking-[-0.025em] text-ink sm:text-[2.6rem]">
          A drafting board for code, not a chat window.
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {steps.map((s) => (
          <article
            key={s.n}
            className="group relative flex flex-col gap-5 rounded-md border border-line bg-surface p-6 transition-colors hover:border-line-strong"
          >
            <div className="flex h-[120px] items-center justify-center border-b border-line pb-5">
              {s.diagram}
            </div>
            <div>
              <p className="font-mono text-[10.5px] font-semibold uppercase tracking-eyebrow text-ink-soft">
                {s.n}
              </p>
              <h3 className="mt-1.5 font-display text-[20px] font-semibold tracking-[-0.015em] text-ink">
                {s.title}
              </h3>
              <p className="mt-3 text-[14px] leading-[1.6] text-ink-muted">
                {s.body}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Preview() {
  return (
    <section className="border-y border-line bg-surface">
      <div className="mx-auto max-w-[1180px] px-6 py-24 sm:px-8 sm:py-28">
        <div className="mb-12 flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-ink-muted">
              On the screen
            </p>
            <h2 className="mt-4 font-display text-[2rem] font-semibold leading-[1.05] tracking-[-0.025em] text-ink sm:text-[2.6rem]">
              Real worktrees. Real diffs. Real merges.
            </h2>
          </div>
          <Link
            to="/app"
            className="inline-flex items-center gap-1.5 font-mono text-[12px] uppercase tracking-eyebrow text-accent hover:text-accent-strong"
          >
            Try the live demo <span aria-hidden>→</span>
          </Link>
        </div>
        <FauxGraphCanvas />
        <p className="mt-5 font-mono text-[11.5px] uppercase tracking-eyebrow text-ink-soft">
          Live: three agents implementing rate limiting on{" "}
          <span className="text-ink-muted">POST /api/login</span> · middleware
          finished, route-local running, dependency queued
        </p>
      </div>
    </section>
  );
}

function BuiltWith() {
  const items = [
    "Claude Agent SDK",
    "Real git worktrees",
    "Live SSE streaming",
    "Side-by-side unified diffs",
    "FastAPI + React + XYFlow",
  ];
  return (
    <section className="mx-auto max-w-[1180px] px-6 py-16 sm:px-8 sm:py-20">
      <p className="font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-ink-muted">
        Under the hood
      </p>
      <ul className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-3 font-mono text-[13px] text-ink-muted sm:text-[14px]">
        {items.map((item, i) => (
          <li key={item} className="flex items-center gap-6">
            <span>{item}</span>
            {i < items.length - 1 && (
              <span aria-hidden className="text-ink-soft">
                ·
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function ClosingCTA() {
  return (
    <section className="border-t border-line">
      <div className="mx-auto max-w-[1180px] px-6 py-28 sm:px-8 sm:py-32">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-ink-muted">
          Ready?
        </p>
        <h2 className="mt-6 max-w-[840px] font-display text-[2.6rem] font-semibold leading-[1.02] tracking-[-0.03em] text-ink sm:text-[3.6rem]">
          Stop trusting the first answer.{" "}
          <em className="font-semibold not-italic text-accent">
            Build it three ways instead.
          </em>
        </h2>
        <p className="mt-6 max-w-[560px] text-[15.5px] leading-[1.65] text-ink-muted">
          Open the workspace and spawn three branches in ten seconds. The demo
          repo is preloaded.
        </p>
        <div className="mt-9 flex flex-wrap items-center gap-3">
          <Link
            to="/app"
            className="inline-flex items-center gap-2 rounded-sm bg-accent px-6 py-3.5 text-[14px] font-semibold text-paper-deep shadow-panel transition-colors hover:bg-accent-strong"
          >
            Open the workspace <span aria-hidden>→</span>
          </Link>
          <Link
            to="/app"
            className="inline-flex items-center gap-2 rounded-sm border border-line-strong bg-surface px-6 py-3.5 text-[14px] font-semibold text-ink transition-colors hover:bg-paper-deep"
          >
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-line bg-paper">
      <div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-3 px-6 py-8 font-mono text-[11px] uppercase tracking-eyebrow text-ink-soft sm:px-8">
        <p>
          Agent Graph ·{" "}
          <span className="text-ink-muted">A branching workspace</span>
        </p>
        <p className="flex items-center gap-5">
          <a href="#" className="hover:text-ink-muted">
            GitHub
          </a>
          <a href="#" className="hover:text-ink-muted">
            Docs
          </a>
          <Link to="/app" className="hover:text-ink-muted">
            Demo
          </Link>
        </p>
      </div>
    </footer>
  );
}

function BrandMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden>
      <circle cx="12" cy="4" r="2" fill="#1a1a1d" />
      <circle cx="4" cy="20" r="1.6" fill="#1a1a1d" opacity="0.5" />
      <circle cx="12" cy="20" r="2" fill="#d8492e" />
      <circle cx="20" cy="20" r="1.6" fill="#1a1a1d" opacity="0.5" />
      <path
        d="M12 6 Q 12 12 4 19"
        stroke="#1a1a1d"
        strokeOpacity="0.45"
        strokeWidth="1.1"
        fill="none"
      />
      <path
        d="M12 6 L 12 18"
        stroke="#d8492e"
        strokeWidth="1.4"
        fill="none"
      />
      <path
        d="M12 6 Q 12 12 20 19"
        stroke="#1a1a1d"
        strokeOpacity="0.45"
        strokeWidth="1.1"
        fill="none"
      />
    </svg>
  );
}

function BranchMotif() {
  return (
    <svg
      viewBox="0 0 320 360"
      className="w-full max-w-[420px]"
      aria-hidden
    >
      <defs>
        <radialGradient id="halo" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#d8492e" stopOpacity="0.18" />
          <stop offset="100%" stopColor="#d8492e" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="160" cy="180" r="140" fill="url(#halo)" />

      <path
        d="M160 36 Q 160 130, 56 312"
        stroke="#1a1a1d"
        strokeOpacity="0.35"
        strokeWidth="1.2"
        fill="none"
      />
      <path
        d="M160 36 L 160 312"
        stroke="#d8492e"
        strokeWidth="1.6"
        fill="none"
      />
      <path
        d="M160 36 Q 160 130, 264 312"
        stroke="#1a1a1d"
        strokeOpacity="0.35"
        strokeWidth="1.2"
        fill="none"
      />

      <circle cx="160" cy="36" r="6" fill="#1a1a1d" />
      <text
        x="170"
        y="32"
        fontFamily="JetBrains Mono, monospace"
        fontSize="10"
        fill="#6b6960"
      >
        main
      </text>

      <circle cx="56" cy="312" r="5" fill="#1a1a1d" fillOpacity="0.6" />
      <text
        x="20"
        y="332"
        fontFamily="JetBrains Mono, monospace"
        fontSize="10"
        fill="#6b6960"
      >
        route_local
      </text>

      <circle cx="160" cy="312" r="6.5" fill="#d8492e" />
      <circle
        cx="160"
        cy="312"
        r="11"
        fill="none"
        stroke="#d8492e"
        strokeOpacity="0.4"
        className="accent-pulse"
      />
      <text
        x="138"
        y="332"
        fontFamily="JetBrains Mono, monospace"
        fontSize="10"
        fill="#d8492e"
      >
        middleware ✓
      </text>

      <circle cx="264" cy="312" r="5" fill="#1a1a1d" fillOpacity="0.6" />
      <text
        x="240"
        y="332"
        fontFamily="JetBrains Mono, monospace"
        fontSize="10"
        fill="#6b6960"
      >
        dependency
      </text>

      <circle r="2.6" className="edge-particle">
        <animateMotion
          dur="1.8s"
          repeatCount="indefinite"
          path="M160 36 L 160 312"
        />
      </circle>
    </svg>
  );
}

function SpawnDiagram() {
  return (
    <svg viewBox="0 0 220 80" className="h-[80px] w-full" aria-hidden>
      <path
        d="M110 12 Q 110 40, 30 70"
        stroke="#1a1a1d"
        strokeOpacity="0.4"
        strokeWidth="1"
        fill="none"
      />
      <path
        d="M110 12 L 110 70"
        stroke="#d8492e"
        strokeWidth="1.2"
        fill="none"
      />
      <path
        d="M110 12 Q 110 40, 190 70"
        stroke="#1a1a1d"
        strokeOpacity="0.4"
        strokeWidth="1"
        fill="none"
      />
      <circle cx="110" cy="12" r="4" fill="#1a1a1d" />
      <circle cx="30" cy="70" r="3.5" fill="#1a1a1d" fillOpacity="0.5" />
      <circle cx="110" cy="70" r="4" fill="#d8492e" />
      <circle cx="190" cy="70" r="3.5" fill="#1a1a1d" fillOpacity="0.5" />
    </svg>
  );
}

function CompareDiagram() {
  return (
    <svg viewBox="0 0 220 80" className="h-[80px] w-full" aria-hidden>
      <rect
        x="20"
        y="14"
        width="80"
        height="52"
        rx="3"
        fill="#fefdfa"
        stroke="#1a1a1d"
        strokeOpacity="0.3"
      />
      <rect
        x="120"
        y="14"
        width="80"
        height="52"
        rx="3"
        fill="#fefdfa"
        stroke="#d8492e"
        strokeWidth="1.2"
      />
      <line x1="32" y1="26" x2="86" y2="26" stroke="#1a1a1d" strokeOpacity="0.25" strokeWidth="1.4" />
      <line x1="32" y1="34" x2="76" y2="34" stroke="#1a1a1d" strokeOpacity="0.25" strokeWidth="1.4" />
      <line x1="32" y1="42" x2="80" y2="42" stroke="#1a1a1d" strokeOpacity="0.25" strokeWidth="1.4" />
      <line x1="32" y1="50" x2="70" y2="50" stroke="#1a1a1d" strokeOpacity="0.25" strokeWidth="1.4" />
      <line x1="132" y1="26" x2="186" y2="26" stroke="#d8492e" strokeOpacity="0.7" strokeWidth="1.4" />
      <line x1="132" y1="34" x2="178" y2="34" stroke="#d8492e" strokeOpacity="0.7" strokeWidth="1.4" />
      <line x1="132" y1="42" x2="182" y2="42" stroke="#d8492e" strokeOpacity="0.7" strokeWidth="1.4" />
      <line x1="132" y1="50" x2="170" y2="50" stroke="#d8492e" strokeOpacity="0.7" strokeWidth="1.4" />
    </svg>
  );
}

function MergeDiagram() {
  return (
    <svg viewBox="0 0 220 80" className="h-[80px] w-full" aria-hidden>
      <path
        d="M30 12 Q 30 40, 110 70"
        stroke="#1a1a1d"
        strokeOpacity="0.3"
        strokeWidth="1"
        fill="none"
      />
      <path
        d="M110 12 L 110 70"
        stroke="#d8492e"
        strokeWidth="1.4"
        fill="none"
      />
      <path
        d="M190 12 Q 190 40, 110 70"
        stroke="#1a1a1d"
        strokeOpacity="0.3"
        strokeWidth="1"
        fill="none"
      />
      <circle cx="30" cy="12" r="3.5" fill="#1a1a1d" fillOpacity="0.5" />
      <circle cx="110" cy="12" r="4" fill="#d8492e" />
      <circle cx="190" cy="12" r="3.5" fill="#1a1a1d" fillOpacity="0.5" />
      <circle cx="110" cy="70" r="5" fill="#1a1a1d" />
    </svg>
  );
}

function FauxGraphCanvas() {
  return (
    <div className="relative overflow-hidden rounded-md border border-line-strong bg-paper-deep shadow-panel">
      <div className="flex items-center justify-between border-b border-line bg-surface px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-danger/80" />
          <span className="h-2 w-2 rounded-full bg-warning/80" />
          <span className="h-2 w-2 rounded-full bg-success/80" />
          <span className="ml-3 font-mono text-[11px] uppercase tracking-eyebrow text-ink-muted">
            agent-graph · /app
          </span>
        </div>
        <span className="font-mono text-[11px] uppercase tracking-eyebrow text-ink-soft">
          ⌘ N · ⌘ R · ⌘ C
        </span>
      </div>

      <div className="relative h-[420px] w-full">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_30%,rgba(216,73,46,0.06),transparent_60%)]" />

        <svg viewBox="0 0 800 420" className="absolute inset-0 h-full w-full" aria-hidden>
          <path d="M400 70 Q 400 180, 180 320" stroke="#1a1a1d" strokeOpacity="0.32" strokeWidth="1.3" fill="none" />
          <path d="M400 70 L 400 320" stroke="#d8492e" strokeWidth="1.6" fill="none" />
          <path d="M400 70 Q 400 180, 620 320" stroke="#1a1a1d" strokeOpacity="0.32" strokeWidth="1.3" fill="none" />
          <circle r="3" fill="#d8492e">
            <animateMotion dur="1.8s" repeatCount="indefinite" path="M400 70 L 400 320" />
          </circle>
          <circle r="2.5" fill="#1a1a1d" fillOpacity="0.5">
            <animateMotion dur="2.2s" repeatCount="indefinite" path="M400 70 Q 400 180, 180 320" />
          </circle>
        </svg>

        <FauxNode
          x="50%"
          y="60px"
          label="main"
          sub="POST /api/login · 4 failing tests"
          tone="ink"
        />
        <FauxNode
          x="22%"
          y="300px"
          label="route_local"
          sub="running · streaming tool calls"
          tone="muted"
        />
        <FauxNode
          x="50%"
          y="300px"
          label="middleware"
          sub="completed · 4/4 tests passing"
          tone="accent"
        />
        <FauxNode
          x="78%"
          y="300px"
          label="dependency"
          sub="queued"
          tone="muted"
        />

        <div className="absolute right-5 top-5 w-[260px] rounded-md border border-line bg-surface p-4 shadow-panel">
          <p className="font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
            agent log · middleware
          </p>
          <ul className="mt-3 space-y-1.5 font-mono text-[11.5px] leading-[1.5] text-ink">
            <li className="text-ink-muted">▸ read app/main.py</li>
            <li className="text-ink-muted">▸ write app/middleware/rate_limit.py</li>
            <li className="text-ink-muted">▸ run pytest tests/test_rate_limit.py</li>
            <li className="text-success">✓ 4/4 tests passing</li>
            <li className="text-accent">⏵ ready to merge</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function FauxNode({
  x,
  y,
  label,
  sub,
  tone,
}: {
  x: string;
  y: string;
  label: string;
  sub: string;
  tone: "ink" | "muted" | "accent";
}) {
  const ring =
    tone === "accent"
      ? "border-accent shadow-[0_0_0_4px_rgba(216,73,46,0.12)]"
      : tone === "ink"
        ? "border-line-strong"
        : "border-line";
  const dot =
    tone === "accent"
      ? "bg-accent"
      : tone === "ink"
        ? "bg-ink"
        : "bg-ink-soft";
  return (
    <div
      className={`absolute -translate-x-1/2 rounded-md border bg-surface px-4 py-3 shadow-panel ${ring}`}
      style={{ left: x, top: y, minWidth: 160 }}
    >
      <div className="flex items-center gap-2">
        <span className={`h-1.5 w-1.5 rounded-full ${dot} ${tone === "accent" ? "accent-pulse" : ""}`} />
        <span className="font-mono text-[12px] font-medium text-ink">{label}</span>
      </div>
      <p className="mt-1.5 font-mono text-[10.5px] leading-[1.4] text-ink-muted">
        {sub}
      </p>
    </div>
  );
}

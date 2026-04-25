/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    // Lock the spacing scale to the seven approved values.
    spacing: {
      0: "0",
      1: "var(--space-1)",  // 4
      1.5: "var(--space-2)", // 6
      2: "var(--space-3)",  // 8
      3: "var(--space-4)",  // 12
      4: "var(--space-5)",  // 16
      6: "var(--space-6)",  // 24
      8: "var(--space-7)",  // 32
      px: "1px",
      // PHASE-2-CLEANUP: temporary whitelist for spacing values used by
      // existing components that will be rebuilt in Phase 2. Each entry is
      // mapped to its original Tailwind default. Remove once components stop
      // using out-of-scale spacing.
      0.5: "2px",
      2.5: "10px",
      5: "20px",
      7: "28px",
      24: "96px",
    },
    fontSize: {
      xs:   ["var(--text-xs)",   { lineHeight: "var(--leading-tight)" }],
      sm:   ["var(--text-sm)",   { lineHeight: "var(--leading-normal)" }],
      base: ["var(--text-base)", { lineHeight: "var(--leading-normal)" }],
      md:   ["var(--text-md)",   { lineHeight: "var(--leading-normal)" }],
      lg:   ["var(--text-lg)",   { lineHeight: "var(--leading-tight)" }],
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
    },
    borderRadius: {
      none: "0",
      sm: "var(--radius-sm)",
      md: "var(--radius-md)",
      lg: "var(--radius-lg)",
      full: "9999px",
    },
    extend: {
      fontFamily: {
        sans: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        display: ['"Inter"', "system-ui", "sans-serif"],
        body:    ['"Inter"', "system-ui", "sans-serif"],
      },
      colors: {
        "bg-canvas":         "var(--color-bg-canvas)",
        "bg-surface":        "var(--color-bg-surface)",
        "bg-surface-raised": "var(--color-bg-surface-raised)",
        "border-subtle":     "var(--color-border-subtle)",
        "border-default":    "var(--color-border-default)",
        "border-strong":     "var(--color-border-strong)",
        "text-primary":      "var(--color-text-primary)",
        "text-secondary":    "var(--color-text-secondary)",
        "text-tertiary":     "var(--color-text-tertiary)",
        "text-disabled":     "var(--color-text-disabled)",
        accent:              "var(--color-accent)",
        "accent-hover":      "var(--color-accent-hover)",
        "accent-fg":         "var(--color-accent-fg)",
        "accent-soft":       "var(--color-accent-soft)",
        "status-idle":       "var(--status-idle-fg)",
        "status-creating":   "var(--status-creating-fg)",
        "status-running":    "var(--status-running-fg)",
        "status-completed":  "var(--status-completed-fg)",
        "status-failed":     "var(--status-failed-fg)",
        "status-merged":     "var(--status-merged-fg)",
        // Backwards-compat aliases:
        paper:               "var(--color-paper)",
        "paper-deep":        "var(--color-paper-deep)",
        surface:             "var(--color-surface)",
        "surface-raised":    "var(--color-surface-raised)",
        ink:                 "var(--color-ink)",
        "ink-muted":         "var(--color-ink-muted)",
        "ink-soft":          "var(--color-ink-soft)",
        line:                "var(--color-line)",
        "line-strong":       "var(--color-line-strong)",
        "accent-strong":     "var(--color-accent-strong)",
        success:             "var(--color-success)",
        "success-soft":      "var(--color-success-soft)",
        danger:              "var(--color-danger)",
        "danger-soft":       "var(--color-danger-soft)",
        warning:             "var(--color-warning)",
        muted:               "var(--color-muted)",
        "strategy-route-local": "var(--strategy-route-local)",
        "strategy-dependency":  "var(--strategy-dependency)",
        "strategy-middleware":  "var(--strategy-middleware)",
      },
      boxShadow: {
        "elev-1": "var(--elev-1)",
        "elev-2": "var(--elev-2)",
        "elev-3": "var(--elev-3)",
        panel:    "var(--elev-1)",
        "panel-lg": "var(--elev-2)",
        hairline: "0 0 0 1px var(--color-border-default)",
        "hairline-strong": "0 0 0 1px var(--color-border-strong)",
      },
      transitionDuration: {
        fast: "var(--dur-fast)",
        base: "var(--dur-base)",
        slow: "var(--dur-slow)",
      },
      letterSpacing: {
        eyebrow: "0.16em",
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        paper: "var(--color-paper)",
        "paper-deep": "var(--color-paper-deep)",
        surface: "var(--color-surface)",
        "surface-raised": "var(--color-surface-raised)",
        ink: "var(--color-ink)",
        "ink-muted": "var(--color-ink-muted)",
        "ink-soft": "var(--color-ink-soft)",
        line: "var(--color-line)",
        "line-strong": "var(--color-line-strong)",
        accent: "var(--color-accent)",
        "accent-strong": "var(--color-accent-strong)",
        "accent-soft": "var(--color-accent-soft)",
        success: "var(--color-success)",
        "success-soft": "var(--color-success-soft)",
        danger: "var(--color-danger)",
        "danger-soft": "var(--color-danger-soft)",
      },
      boxShadow: {
        panel: "0 1px 0 rgba(26, 26, 29, 0.04), 0 8px 24px rgba(26, 26, 29, 0.05)",
        "panel-lg": "0 1px 0 rgba(26, 26, 29, 0.05), 0 18px 44px rgba(26, 26, 29, 0.08)",
      },
      borderRadius: { DEFAULT: "6px", sm: "4px", md: "8px", lg: "12px", xl: "16px" },
      letterSpacing: {
        eyebrow: "0.16em",
      },
    },
  },
  plugins: [],
};

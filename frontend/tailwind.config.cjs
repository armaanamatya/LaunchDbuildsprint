/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', '"Segoe UI"', "sans-serif"],
        body: ['"IBM Plex Sans"', '"Segoe UI"', "sans-serif"],
      },
      colors: {
        ink: "var(--color-ink)",
        paper: "var(--color-paper)",
        accent: "var(--color-accent)",
        muted: "var(--color-muted)",
        line: "var(--color-line)",
      },
      boxShadow: {
        panel: "0 18px 40px rgba(24, 24, 27, 0.08)",
      },
    },
  },
  plugins: [],
};

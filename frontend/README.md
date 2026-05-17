# Agent Graph Frontend

React + Vite + Tailwind. Renders the graph workspace, subscribes to SSE for live agent output, and provides the side-by-side compare view. See [the root README](../README.md) for the project overview.

## Run

```bash
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. The backend must be running on port 8000 (`cd ../backend && uv run uvicorn app.main:app --reload`).

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | `tsc --noEmit` then `vite build` to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm test` | Run vitest once |
| `npm run test:watch` | Vitest in watch mode |

## Routes

- `/` — editorial landing page (`src/landing/`)
- `/app` — the graph workspace (`src/App.tsx`, `src/components/`)

## Layout

```
src/
├── App.tsx              Workspace shell — toolbar, graph, side rail, compare
├── main.tsx             Router + providers
├── index.css            Tailwind entry + token import
├── landing/             Static landing page
├── components/          GraphCanvas, NodeCard, ComparePanel, StatusBadge, etc.
├── store/               Zustand store — graph state, SSE handlers
├── api/                 fetch wrappers around the backend REST + SSE
├── hooks/               useGraphStream, useNodeStream
├── types.ts             TypeScript mirror of backend Pydantic models
└── styles/tokens.css    Design token source of truth
```

## Design tokens

The styling system is documented in [`docs/tokens.md`](docs/tokens.md). Short version: there is one accent color with one purpose per screen, six status colors that may not be used outside status indicators, and a small fixed spacing/type scale. Tailwind reads from `src/styles/tokens.css` via `tailwind.config.cjs`.

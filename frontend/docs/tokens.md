# Agent Graph Design Tokens

Single source of truth: `src/styles/tokens.css`. Tailwind reads from these vars via `tailwind.config.cjs`. Components should consume tokens through Tailwind utility classes; raw `var(--token-name)` is acceptable for cases Tailwind can't express (gradients, status row backgrounds).

## Surfaces

| Token | Use |
|---|---|
| `--color-bg-canvas` | Outermost background, the graph canvas. Tailwind: `bg-bg-canvas`. |
| `--color-bg-surface` | Top bar, side rail, base panels. Tailwind: `bg-bg-surface`. |
| `--color-bg-surface-raised` | Cards (nodes, modals), elevated above surface. Tailwind: `bg-bg-surface-raised`. |

## Borders

| Token | Use |
|---|---|
| `--color-border-subtle` | Internal dividers inside a panel. |
| `--color-border-default` | Default panel/card borders. |
| `--color-border-strong` | Hover state, selected state outline. |

## Text

| Token | Use |
|---|---|
| `--color-text-primary` | Headlines, labels, primary content. |
| `--color-text-secondary` | Captions, secondary metadata. |
| `--color-text-tertiary` | Timestamps, hints, disabled-by-context labels. |
| `--color-text-disabled` | Truly disabled text. |

## Accent

The accent color (`#4f8cff`) has **one purpose per screen**. Default purpose: the primary action button (`Run`). Do not use accent on hover backgrounds, borders, or non-primary buttons. Accent on text is reserved for active tab underlines and selected-state node borders.

## Status palette (six values, six hues)

Each status has `--status-<name>-fg`, `--status-<name>-bg`, `--status-<name>-border`.

| Status | Hue | Backend enum mapping |
|---|---|---|
| `idle`      | neutral gray   | `idle` |
| `creating`  | dim cyan       | **`queued`** (backend) — visual treatment is "creating" |
| `running`   | amber          | `running` |
| `completed` | calm green     | `completed` |
| `failed`    | desaturated red| `failed` |
| `merged`    | muted purple   | `merged` |

**Status enum mismatch.** The backend ships `queued`, the spec calls this state `creating`. We render the `queued` backend value with the `creating` palette. Helper `statusPalette(node.status)` lives in `src/components/StatusBadge.tsx` (introduced in Phase 2).

**Color carries meaning.** No element outside a status indicator (badge, dot, edge-running) may use a status color. Status colors never decorate non-status surfaces.

## Type scale

Five sizes only: `xs 11`, `sm 12`, `base 13`, `md 14`, `lg 16`. Three weights: 400, 500, 600. Use `font-mono` for code, IDs, branch names, timestamps, and pill labels.

## Spacing

Allowed values only: `1 (4)`, `1.5 (6)`, `2 (8)`, `3 (12)`, `4 (16)`, `6 (24)`, `8 (32)`. Anything else is a bug. (Some additional values may be temporarily whitelisted in tailwind.config.cjs as `// PHASE-2-CLEANUP` until the offending components are rebuilt in Phase 2.)

## Radii

`sm 4` for small chips and pills; `md 6` for cards, nodes, panels; `lg 8` for modals.

## Elevations

Three levels: `elev-1`, `elev-2`, `elev-3`. Use `elev-1` for default cards, `elev-2` for hover/selected, `elev-3` for modals/dialogs only.

## Motion

Durations: `fast 120ms` (micro-interactions), `base 180ms` (state changes), `slow 280ms` (modal opens). Easings: `ease-out` for enters, `ease-in` for exits, `ease-in-out` for state changes. Nothing animates longer than 280ms.

## Compare-tab placement

Spec calls for a Logs/Diff/Compare tab strip in the right panel. Implementation: Compare tab shows a staging UI (compare-pinned nodes + "Open compare" CTA). The actual side-by-side compare is the fullscreen ComparePanel — 380px right rail is too narrow for 2-3 diff columns.

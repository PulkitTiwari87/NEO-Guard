# Design System

> **Status: IMPLEMENTED — Phase 3.5 (Planetary Defense Command Console, aerospace HUD theme)**
>
> Replaces the Phase 3 "Apple-inspired scientific dark theme" entry below (kept for history).
> Visual source of truth: the Stitch-generated "NEO-Guard Planetary Defense Command Dashboard"
> screen (Stitch project `AI Receptionist Admin Dashboard`, screen id
> `dd2f8afb3c844b8782fc8825a88ef174`) plus its companion `DESIGN.md`. See
> `docs/STITCH_IMPLEMENTATION.md` for the full inspection record and what was
> deliberately changed for scientific-integrity reasons.

## Visual Foundations & Design Philosophy

- **Mission-console aesthetic**: dense, technical, monospace-forward telemetry styling —
  restrained brutalist corners (max `0.25rem` on cards), no pill buttons, no gradients or
  glassmorphic glow beyond a single `hud-bracket` corner-tick treatment.
- **Cyan-first data hierarchy**: real, primary data is cyan; violet marks a secondary orbit
  class; amber marks hazard/experimental/caution states. Non-hazardous/nominal status uses a
  calm desaturated teal rather than green, keeping the palette to a disciplined cyan family
  plus one warning hue (an intentional deviation from a generic red/green traffic-light scheme).
- **Reuse over reinvention**: existing semantic Tailwind tokens (`canvas`, `surface`, `border`,
  `accent`, `muted`, `hazard`, `safe`) were re-valued in place rather than renamed, so the
  retheme is a config/token change, not a rewrite of every component.

## Design Tokens

Defined in `frontend/tailwind.config.js` (`theme.extend.colors`) and `frontend/src/index.css`.

### Color Palette

| Token | Hex / rgba | Purpose |
|---|---|---|
| `canvas` | `#101319` | App background, under a 4%-opacity cyan grid (`.tactical-grid`, applied globally on `body`) |
| `surface` | `#0b0e13` | Card/panel background |
| `surface-raised` | `#191c21` | Inputs, nested rows, sidebar |
| `surface-overlay` | `#1d2025` | Modals/overlays |
| `surface-high` / `surface-highest` | `#272a30` / `#32353b` | Hover states, progress-track backgrounds |
| `border` | `rgba(58,73,75,0.4)` (outline-variant) | Card/panel borders |
| `border-strong` | `rgba(132,148,149,0.55)` (outline) | Emphasized borders |
| `accent` | `#00f2ff` (radar cyan) | Primary data, active nav, primary buttons |
| `secondary` | `#cfbdff` (orbital violet) | Secondary orbit class (AMO), secondary data series |
| `hazard` | `#ffb86f` (warning amber) | PHA flag, experimental model status, warnings |
| `safe` | `#7dd8de` (desaturated teal) | Non-hazardous / nominal / production status |
| `muted` | `#849495` (outline) | Secondary text, labels |

### Typography

Fonts loaded in `frontend/src/index.css` via Google Fonts:

- **Space Grotesk** (`font-heading`) — page titles and section headings (`text-display`,
  `text-heading`, `text-subheading` combined with `font-heading`).
- **Geist** (`font-sans`, the default body font) — body copy, descriptions.
- **JetBrains Mono** (`font-mono`) — all numeric/telemetry values, designations, dates, badges,
  nav labels, table cells: anywhere a real measured or identifying value appears.

### Shapes

`borderRadius.card` reduced from `0.75rem` (Phase 3) to `0.25rem`. `Badge`/`Button`/icon
containers switched from `rounded-full`/`rounded-lg` to `rounded`/`rounded-md` — no pill
geometry, per the Stitch brand guidance ("avoid high-radius or pill geometries, which
compromise the scientific authority of the interface").

### HUD treatment

`.hud-bracket` (in `index.css`) adds 1.5px cyan corner tick marks to every `Card` and the new
`HudPanel` component — the one decorative flourish kept from the Stitch reference, applied via
a single shared CSS class rather than repeated per component.

## Component Architecture

1. **`CommandHeader`** (new) — sticky top bar: brand, real global search (routes to
   `/neos?q=`), real nav (from `components/layout/navItems.ts`), a live `useHealth()`-derived
   status pill, and the mobile menu/drawer. Replaces the old `MobileNav` (deleted — its drawer
   was folded in here to avoid duplicating the nav-item list).
2. **`Sidebar`** — desktop command rail: real system-status line (from `useHealth`), real
   dataset version (from `useModels`), a link to the live `/openapi.json`. The Stitch
   reference's fabricated "SECTOR 04-SOL / DEFCON 2" status and "LOG ENCOUNTER" button were
   removed (no such capability exists).
3. **`HudPanel`** (new, `components/dashboard/`) — shared panel shell (title, icon, meta,
   bordered body) used by the four new Dashboard components below.
4. **`OrbitalRadar`** (new) — schematic SVG plot of real `upcoming_close_approaches`, explicitly
   labeled as a non-live projection (Phase 3.5 §13 requires this disclaimer).
5. **`CloseApproachMatrix`** (new) — real close-approach table; a "Hazard Flag" column
   (PHA/NON-PHA/UNKNOWN from real data) replaces the reference's fabricated "Defense Status"
   ("TELEMETRY LOCKED" / "SIMULATED DART VECTOR").
6. **`DataSourcesPanel`** (new) — replaces the reference's fabricated "Sensor Array Telemetry"
   (no real telescope feed exists) with the two real, documented NASA/JPL sources and their
   real record counts.
7. **`QuickActionsPanel`** (new) — replaces the reference's "Tactical Intervention Toolbar"
   (deflection simulation / orbit recalculation / MPC export do not exist) with links to real
   features only: Prediction, Analytics, Methodology.
8. **`Card` / `Badge` / `Button` / `EmptyState` / `Spinner` / `Charts`** — retained, retoned to
   the new tokens in place (see `docs/STITCH_IMPLEMENTATION.md` for the full file list).

---

## Phase 3 entry (superseded, kept for history)

> **Status: SUPERSEDED — see the Phase 3.5 entry above.**

The Phase 3 frontend implemented an Apple-inspired scientific dark theme: `#080B11` canvas,
`#0D1117` cards, Inter + JetBrains Mono typography, and a red/green/amber semantic palette.
It was replaced in Phase 3.5 by the aerospace command-console theme above, built around a real
Stitch-generated reference rather than an original design direction.

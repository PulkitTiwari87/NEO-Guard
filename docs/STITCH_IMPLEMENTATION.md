# Stitch Implementation Report — Phase 3.5

## STITCH MCP STATUS

**AVAILABLE.** `mcp__stitch__list_projects` and `mcp__stitch__list_screens` were used to locate
the actual generated design. The reference image supplied by the user corresponds to a Stitch
project titled **"AI Receptionist Admin Dashboard"** (`projects/3559954832578184129` —
generic/leftover title, but the most-recently-updated Stitch project at the time of this
session), which contains a screen literally named **"NEO-Guard Planetary Defense Command
Dashboard"** (`screens/dd2f8afb3c844b8782fc8825a88ef174`). That screen's real generated HTML
(Tailwind config + markup, ~46 KB) was downloaded and read in full — not reverse-engineered from
the screenshot alone — via its `htmlCode.downloadUrl`. The user also supplied a companion
`DESIGN.md` (design tokens + brand prose) from the same Stitch export, read directly.

## REFERENCE SCREEN

- Project: `projects/3559954832578184129` ("AI Receptionist Admin Dashboard")
- Screen: `screens/dd2f8afb3c844b8782fc8825a88ef174`, title "NEO-Guard Planetary Defense Command
  Dashboard", desktop, 2560×2918.
- Companion tokens: `DESIGN.md` (colors, typography, spacing, elevation, component guidance —
  Material-3-style token names: `surface-container-lowest`, `primary-container`, etc.)

## DESIGN TOKENS EXTRACTED

Read directly from the screen's own `tailwind.config` script tag (ground truth, not
approximated from pixels):

- Colors: `background #101319`, `surface-container-lowest #0b0e13`, `surface-container-low
  #191c21`, `surface-container #1d2025`, `surface-container-high #272a30`,
  `surface-container-highest #32353b`, `primary-container #00f2ff` (radar cyan),
  `primary-fixed-dim #00dbe7`, `secondary #cfbdff` (orbital violet), `tertiary-fixed-dim #ffb86f`
  (warning amber), `outline #849495`, `outline-variant #3a494b`.
- Fonts: Space Grotesk (headlines), Geist (body), JetBrains Mono (labels/telemetry), Material
  Symbols Outlined (icons).
- Border radius: `DEFAULT 0.125rem`, `lg 0.25rem`, `xl 0.5rem`, `full 0.75rem` (their "full" is
  not an actual circle — brutalist, anti-pill).
- Custom CSS: `.tactical-grid` (4%-opacity cyan grid background), `.hud-bracket` (corner tick
  marks), a `radar-sweep` keyframe animation.

## COLOR SYSTEM

Implemented in `frontend/tailwind.config.js` by re-valuing the **existing** semantic tokens in
place (`canvas`, `surface.*`, `border.*`, `accent.*`, `muted.*`, `hazard.*`, `safe.*`) rather than
introducing Stitch's raw Material-3 token names — this kept every existing component working
with only a config change plus a handful of hardcoded-hex fixes (see below), instead of a
find/replace across the whole codebase. One new token, `secondary` (orbital violet), was added
for the one place Stitch uses a third data color (the AMO orbit class / secondary series).

## TYPOGRAPHY

Space Grotesk / Geist / JetBrains Mono all added via `frontend/src/index.css`'s Google Fonts
`@import`. Space Grotesk is exposed as `font-heading` and applied to page/section headings
(`text-display`, `text-heading`, `text-subheading` usages). Geist replaced Inter as the default
`font-sans` body font. JetBrains Mono (already present in Phase 3) is now used far more broadly:
every badge, nav label, table cell, and KPI value.

## LAYOUT

Implemented per Stitch: a sticky top `CommandHeader` (brand, search, nav, status) plus a
left `Sidebar` rail, with the page content in a 12-column grid on the Dashboard (8 cols main /
4 cols right rail on `xl+`, stacking to 1 column below that) — matching the reference's
structure. `Icon` choice deviates: the reference uses Google's Material Symbols web font;
this app kept `lucide-react` (already a project dependency, tree-shakeable SVGs) rather than
add a second icon system for one screen — an intentional, documented deviation (§26/§16 of the
Phase 3.5 prompt: minimal dependencies, no addition without a concrete reason).

## COMPONENTS

New, under `frontend/src/components/`:

- `layout/CommandHeader.tsx`, `layout/navItems.ts` (shared nav config)
- `dashboard/HudPanel.tsx`, `dashboard/OrbitalRadar.tsx`, `dashboard/CloseApproachMatrix.tsx`,
  `dashboard/DataSourcesPanel.tsx`, `dashboard/QuickActionsPanel.tsx`

Retoned in place (colors/radii only, no logic change unless noted):
`components/layout/Sidebar.tsx` (rewritten: real status/dataset, fake DEFCON/LOG ENCOUNTER
removed), `components/layout/AppShell.tsx` (header integration), `components/common/Card.tsx`,
`Badge.tsx`, `Button.tsx`, `EmptyState.tsx`, `components/charts/Charts.tsx` (hardcoded hex
colors — Recharts can't consume Tailwind classes), `pages/Dashboard.tsx` (rebuilt around the
new components), `pages/NeoExplorer.tsx` (added `?q=` URL param support so the new header
search actually works).

Deleted: `components/layout/MobileNav.tsx` — its drawer was folded into `CommandHeader` to
avoid maintaining two copies of the nav-item list (DRY; Phase 3.5 §26).

## DATA-DRIVEN COMPONENTS

Everything above renders only real backend data:

- KPI cards: real `total_neos`, `hazardous_count`, `total_approaches`, model count.
- `OrbitalRadar` / `CloseApproachMatrix`: real `upcoming_close_approaches` (see below — a small,
  documented backend addition).
- `DataSourcesPanel`: real `total_neos`/`total_approaches` counts and real `dataset_version`.
- Orbit class chart: existing real `orbit_class_counts`.
- "Close Approaches by Year": existing real `approaches_by_year` time series, restyled into the
  HUD panel in place of Stitch's fabricated velocity/perturbation curve.

**Backend change (small, justified, per Phase 3.5 §34):** `GET /api/analytics` gained one
additive field, `upcoming_close_approaches` — the soonest ≤8 stored close approaches at/after
now, sorted ascending, each nesting the existing `NeoSummary`/`Approach` schemas. This was the
one piece of real data the Dashboard's radar and encounter-matrix panels needed that no existing
endpoint exposed. Implemented in `backend/app/services/analytics_service.py` +
`backend/app/schemas/analytics.py`; documented in `docs/API_CONTRACT.md`; tested in
`tests/integration/test_api.py`
(`test_upcoming_close_approaches_are_real_stored_rows_sorted_ascending`, plus an empty-DB
assertion). Full backend suite re-run and green (139/139) after the change.

## UNAVAILABLE DATA (Stitch elements NOT reproduced as fabricated)

Per Phase 3.5 §14/§15/§18/§28 ("no fake data" is a hard rule), these Stitch panels were **not**
copied as-is because the underlying data or capability does not exist in this system:

| Stitch element | Why it was replaced | What replaced it |
|---|---|---|
| "Spectral Classification" (C/S/M-type %) | No spectral-type column exists anywhere in the schema or ingestion pipeline | Real "Orbit Class Distribution" chart (already existed, reused in the same panel slot) |
| "Sensor Array Telemetry" (Goldstone/NEOWISE/Catalina/Rubin latency, dish frequency, etc.) | No real telescope/sensor feed is ingested — these are fictional stations with fabricated latency numbers | `DataSourcesPanel`: the two real JPL APIs actually used, with real record counts |
| "Tactical Intervention Toolbar" (RUN DEFLECTION SIMULATION / RECALCULATE ORBIT / EXPORT MPC REPORT) | None of these capabilities exist; DART deflection, orbit re-integration, and MPC export are not implemented anywhere in the backend | `QuickActionsPanel`: real links to Prediction, Analytics, and Methodology, plus the existing scientific disclaimer |
| "SECTOR 04-SOL / STATUS: DEFCON 2 / ELEVATED" sidebar header | Fabricated threat-level status with no backing data | Real `useHealth()`-derived "SYSTEM OPERATIONAL/DEGRADED" |
| "LOG ENCOUNTER" button | No write/logging endpoint exists | Removed |
| "SENSOR OVERRIDE" / "DEFLECTION SIM" header buttons + fictional avatar image | No such capabilities or user accounts exist | Replaced with the real health status pill; avatar dropped entirely (no auth system — an avatar would imply a logged-in identity that doesn't exist) |
| Close-approach "Defense Status" (`TELEMETRY LOCKED`, `SIMULATED DART VECTOR`, `MONITORED`) | Fabricated, meaningless states | Real "Hazard Flag" column (PHA / NON-PHA / UNKNOWN from JPL's actual flag) |
| Radar "EPOCH SCRUBBER" / "LOCK TARGET RETICLE" / "PERTURBATION MESH" controls | Implies live simulation/targeting capability that doesn't exist | Dropped; radar is a static, honestly-labeled schematic |

## INTENTIONAL DEVIATIONS

- Material Symbols icon font → kept `lucide-react` (no new dependency).
- "Safe / Non-PHA" color: a desaturated teal (`#7dd8de`) rather than green — Stitch's own
  palette has no green; introducing one would break the disciplined cyan/violet/amber scheme,
  so non-hazardous status stays in the cyan family (documented in `docs/DESIGN_SYSTEM.md`).
- Nav labels keep the Stitch "command" flavor (e.g. "Orbital Trajectories" for the NEO catalog)
  but map to the app's real routes exactly per Phase 3.5 §11 — no capability implied that the
  route doesn't provide.
- One additive backend field (`upcoming_close_approaches`) — see above.

## VISUAL VERIFICATION

Performed live in a real browser (Claude's built-in Browser pane) against the running dev
server and the real Docker backend, not just described:

- Dashboard: screenshotted at each scroll position; matches the reference's layout (header,
  rail, KPI row, radar hero, trajectory chart, encounter matrix, right rail) with all-real data
  confirmed against direct API responses.
- NEO Explorer, NEO Detail (Apophis), Analytics, Models, Prediction, About: each opened and
  screenshotted; consistent token cascade (no leftover blue/old-theme colors — verified by
  `grep` for hex literals across `frontend/src`, and by visual check after finding and fixing
  one dev-server cache staleness issue).
- Mobile (375×812): Dashboard and NEO Explorer checked; header collapses to a hamburger drawer
  with the same real search + nav; KPI cards stack to 2 columns; tables scroll horizontally
  (pre-existing behavior, unaffected by the retheme).
- Recharts colors (Orbit Class bars, Close-Approaches-by-year line, SHAP bars, hazard donut)
  were hardcoded hex values Tailwind classes cannot reach — found by visual inspection (still
  rendering old blue after the token change) and fixed with named constants in `Charts.tsx`.

## ENGINEERING VERIFICATION

- `tsc --noEmit`: 0 errors (checked after every major edit, not just at the end).
- `eslint --max-warnings 0`: 0 errors/warnings.
- `vitest run`: 18/18 passed, unchanged from before this phase.
- `vite build`: succeeds (716.97 kB main bundle uncompressed, 202 kB gzip — a pre-existing,
  unaddressed bundle-size note, not a regression from this phase; still no code-splitting).
- Backend: `pytest` 139/139 passed (137 non-Postgres, including the 1 new test, + 2 Postgres-marker,
  reproduced against a real Docker Postgres instance), `ruff check` clean.

## KNOWN LIMITATIONS

- No automated visual-regression/E2E suite exists; verification above was manual (browser pane),
  consistent with the project's documented state (`docs/TESTING.md`: "Not yet tested: Frontend
  and browser E2E").
- The `OrbitalRadar`'s pin layout is a schematic (hash-derived angle, real-data-derived radius),
  not true orbital mechanics — labeled as such in the UI itself, per Phase 3.5 §13.
- Bundle size (main chunk >500 kB) was already a pre-existing note in
  `docs/VERIFICATION_REPORT.md`; not addressed in this phase (out of scope: visual/data work only).

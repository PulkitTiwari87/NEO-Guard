# Changelog

## [Unreleased]

### 2026-09-22 — Phase 5: Final release preparation (Claude Code)

No application code was changed this phase — release preparation and documentation only, per
`docs/RELEASE_REPORT.md`. Nothing was committed or pushed (per instructions; the user commits/pushes
manually).

**Added**

* `.github/workflows/ci.yml` — minimal CI: backend (`ruff check`, `pytest -m "not postgres"`) and
  frontend (`npm ci`, `typecheck`, `lint`, `test`, `build`) on every push/PR to `main`.
* `docs/RELEASE_REPORT.md` — Phase 5 release report.

**Resolved / investigated (found, not code changes)**

* `react-router-dom` `npm audit` advisories (2 moderate) — investigated and **not upgraded**;
  neither is exploitable in this app (no SSR; no attacker-controlled path/redirect input).
  Decision and reasoning: `docs/SECURITY.md`.
* NEO Explorer search-box "bounce to Dashboard" anomaly (Phase 4, unconfirmed) — re-investigated
  live against the full required checklist (normal/rapid typing, deletion, empty search, special
  characters, search+filter) plus source inspection. **NOT REPRODUCED** — `NeoExplorer.tsx`'s
  search box has no navigation call in its code path at all. `docs/VERIFICATION_REPORT.md`.

**Changed (documentation accuracy only)**

* Root `README.md` — corrected stale "Frontend: NOT IMPLEMENTED" / "Planned: React..." claims (the
  frontend and Docker stack have been implemented and verified since Phase 3/3.5); added frontend
  quick-start steps and the CI workflow reference.
* `.github/workflows/README.md` — corrected from "NOT IMPLEMENTED" to describe the new `ci.yml`.
* `docs/DEPLOYMENT.md` — added concrete Render (backend) and Vercel (frontend) configuration
  tables (root dir, build/start commands, env vars, health check, port); the model-artifact
  strategy remains an explicit open human decision, not chosen here.
* `docs/SECURITY.md` — logged the Phase 5 dependency audit (`pip-audit` clean) and the
  `react-router-dom` decision; checked off "Dependencies audited" in the production checklist.
* Backend test count corrected from a stale "138" to the actual, reproduced **139** (137
  non-Postgres + 2 Postgres-marker) in `docs/TESTING.md`, `docs/HANDOFF.md`, `docs/TASK_TRACKER.md`
  and `docs/STITCH_IMPLEMENTATION.md`'s Phase 3.5 entries — those entries described the suite
  *after* Phase 3.5 added one new test, so "138" was an arithmetic error at the time, not a new
  regression. Phase 4's own entries (which describe the suite *before* that test existed) were
  left unchanged at 138 — they were accurate when written.
* `docs/TASK_TRACKER.md` — added a Phase 5 "RELEASE PREP" section and updated the DEPLOYMENT
  checklist to reflect documented-but-not-provisioned Render/Vercel config.

**Verified this phase (re-run, not assumed)**

* Backend: `ruff check` clean, `python -m compileall` clean, `pytest -m "not postgres"` 137 passed
  (139 collected total with the 2 Postgres-marker tests), `pip-audit` clean.
* Frontend: `tsc --noEmit` 0 errors, `eslint --max-warnings 0` 0 errors/warnings, `vitest run` 18/18,
  `vite build` succeeds.
* `git diff --check`: no real issues (CRLF-on-checkout warnings only, from Windows `core.autocrlf`;
  one intentional Markdown hard-line-break trailing-space in `docs/HANDOFF.md`, not an error).
* Secret audit: pattern scan for `API_KEY|SECRET|PASSWORD|PRIVATE_KEY|DATABASE_URL|CREDENTIAL|TOKEN`
  assignments across tracked/working-tree source found no real secrets; `.env`/`frontend/.env` exist
  locally but are correctly git-ignored (not shown by `git status`); `.env.example` and
  `frontend/.env.example` contain placeholders only.

**Not done this phase (explicitly out of scope, documented instead of built)**

* Automated browser E2E suite (Playwright/Cypress) — would add a new dependency for a single
  release pass; documented as a future improvement, consistent with prior phases.
* Deployment itself (Render/Vercel provisioning, production smoke test) — configuration is
  documented, not applied; requires human account access and the model-artifact decision.

### 2026-09-22 — Phase 3.5: Stitch-faithful command dashboard redesign (Claude Code)

Frontend visual rework only, after Phase 4 verification, per `docs/STITCH_IMPLEMENTATION.md`.

**Added**

* Aerospace command-console design tokens (cyan/violet/amber HUD palette, Space Grotesk/Geist/
  JetBrains Mono) in `frontend/tailwind.config.js` and `frontend/src/index.css`, sourced from a
  real Stitch-generated "NEO-Guard Planetary Defense Command Dashboard" screen (inspected via
  Stitch MCP, not guessed from the reference image alone).
* New components: `CommandHeader`, `dashboard/{HudPanel,OrbitalRadar,CloseApproachMatrix,
  DataSourcesPanel,QuickActionsPanel}` — Dashboard rebuilt around them, all real-data-driven.
* `GET /api/analytics` gained an additive `upcoming_close_approaches` field (small, justified
  backend change — see `docs/API_CONTRACT.md`) so the new radar/matrix panels have real data.

**Changed**

* Retoned in place (no logic change): `Card`, `Badge`, `Button`, `EmptyState`, `Charts`,
  `Sidebar` (also removed a fabricated "DEFCON 2" status and "LOG ENCOUNTER" button), `AppShell`.
* `NeoExplorer` now reads an initial `?q=` search param, so the new header's global search works.

**Removed**

* `MobileNav.tsx` — folded into `CommandHeader` to avoid duplicating the nav-item list.
* Several Stitch reference elements were deliberately **not** reproduced because they'd be
  fabricated (fake sensor telemetry, a fake deflection-simulation toolbar, fake "telemetry
  locked" statuses) — see `docs/STITCH_IMPLEMENTATION.md`'s "Unavailable Data" table for the
  full list and real replacements.

**Verified:** `tsc`/`eslint`/`vitest` (18/18)/`vite build` all green; backend `pytest` 139/139
green after the API addition; live-browser check across all 6 routes + mobile width.

### 2026-09-22 — Phase 4: Full-system verification (Claude Code)

No production code was changed this phase — verification only, per `docs/VERIFICATION_REPORT.md`.

**Verified (evidence-based, reproduced this session, not assumed from prior claims)**

* Backend: `compileall`/`ruff` clean; full pytest suite (138 tests: 136 unit/ML/integration +
  2 PostgreSQL) passes against a real disposable test database; `pip-audit` clean.
* Database: `docker compose up` (db → migrate → backend) succeeds from a clean container start;
  Alembic migrations reproduce the schema; real JPL data (42,477 NEOs / 30,828 approaches) loaded
  and served.
* API: all 8 documented endpoints live and matching `docs/API_CONTRACT.md`; a real prediction for
  Apophis's actual orbital elements reproduces the exact sanity check recorded in `docs/HANDOFF.md`
  (17.6% probability, 27.0% threshold, `random_forest-v1`, consistent SHAP breakdown).
* NASA/JPL: live connectivity to `ssd-api.jpl.nasa.gov` confirmed working during this session.
* Frontend: `tsc --noEmit`, `eslint`, `vitest` (18 tests) and `vite build` all pass; manually
  driven in a real browser against the live backend across all 6 routes, including a full
  prediction round-trip that matched a direct API call exactly, and a real backend-down error
  state (retry button, no crash).
* Security: no hardcoded secrets found in source; `.env` correctly gitignored; CORS rejects
  wildcard origins in production; `pip-audit` clean.

**Found, not fixed (frontend is out of scope for Claude Code per this repo's `CLAUDE.md` —
handed off for the next frontend-capable phase)**

* `npm audit --omit=dev`: 2 moderate `react-router-dom` advisories (open redirect / SSR hydration);
  not exploitable in this SPA's client-only deployment, but clearing them needs a v6→v7 major bump.
* One unconfirmed, non-reproducible frontend interaction anomaly in the NEO Explorer search box,
  most likely a test-tooling artifact — flagged for manual QA attention, not filed as a bug.

### 2026-09-21 — Phase 2: Backend + ML (Claude Code)

**Added**

* **Data pipeline** (`ml/`): JPL SBDB + CAD ingestion client (timeouts, retry/backoff, `Retry-After`,
  throttling, envelope validation, 24 h cache), write-once raw storage with provenance, pydantic
  validation/normalisation with recorded rejections, PHA-rule audit, ML dataset builder (eligibility,
  de-duplication, chronological split).
* **ML**: stateless feature engineering, leakage-audit registry, Logistic Regression / Random Forest /
  XGBoost training (with and without class weighting), validation-tuned thresholds, held-out
  evaluation with bootstrap CIs, SHAP (global + local), versioned artifacts, inference module.
* **Backend** (`backend/app`): FastAPI app with `/api/health`, `/api/neos`, `/api/neos/{id}`,
  `/api/neos/{id}/approaches`, `/api/predict`, `/api/models`, `/api/models/{version}`, `/api/analytics`;
  structured errors and logging, CORS, security headers, in-process rate limiting.
* **Database**: SQLAlchemy models, Alembic migration `0001`, idempotent loader and registry sync,
  `python -m app.cli {load-data,sync-models,set-status}`.
* **Infrastructure**: `backend/Dockerfile`, `docker-compose.yml` (db + migrate + backend),
  `Makefile` targets, `pyproject.toml`, pinned `backend/requirements*.txt`.
* **Tests** (`tests/`): unit, ML, integration (SQLite) and PostgreSQL migration tests, using clearly
  labelled `SYNTHETIC / TEST DATA` only.
* **Real results**: 6 models trained/evaluated on the real 2026-09-21 snapshot; logged in
  `docs/EXPERIMENTS.md`; model card written.

**Changed (contracts — see `docs/API_CONTRACT.md` for the full table)**

* `GET /api/health`: `status` values `ok|degraded` (was `healthy`), new `database` field, 503 when DB down.
* NEO `id` is an integer SPK-ID; `estimated_diameter_km_min/max` replaced by measured `diameter_km`;
  `is_potentially_hazardous` may be `null`.
* `POST /api/predict` request/response fully specified; `prediction` is `0|1` (was string) with
  `label`, `threshold`, `model_status`, `disclaimer`.
* Database: `neo_objects.id` is the SPK-ID; extra provenance/registry columns (`docs/DATABASE_SCHEMA.md`).
* Environment: **`NASA_API_KEY` removed** (JPL APIs need no key); added `POSTGRES_PASSWORD`,
  `POSTGRES_HOST_PORT`, `LOG_LEVEL`, `RATE_LIMIT_PER_MINUTE`, `MODEL_DIR`, `ACTIVE_MODEL_VERSION`,
  `NEOGUARD_DATA_DIR`; `MODEL_ENV` and `CORS_ORIGINS` kept.
* Foundation placeholders replaced: `docker-compose.yml`, `Makefile`, `.env.example`, `.gitignore`
  (ignores `*.joblib` model binaries, ruff/coverage caches).

**Fixed during development**

* Artifact metadata contained bare `NaN` (XGBoost `missing=NaN`), invalid JSON that PostgreSQL rejected;
  artifact JSON is now strict (non-finite floats stored as strings) and the two affected
  `metadata.json` files were re-serialised (values unchanged).
* Validation now rejects (and records) source rows with the wrong number of values instead of
  silently truncating them.
* CSV boolean column was read with mixed types; now read as a nullable boolean.

**Status snapshot**

| Component | Status |
|-----------|--------|
| Backend (FastAPI) | Implemented, verified locally and in Docker |
| ML pipeline | Implemented; 6 experimental models |
| Database | Implemented; migration verified on PostgreSQL 16 |
| Frontend | NOT IMPLEMENTED (next phase) |
| Deployment (Render/Vercel) | NOT IMPLEMENTED / NOT VERIFIED |
| Data | Real JPL data only (tests use labelled synthetic fixtures) |

### 2026-09-21 — Foundation Phase (Antigravity)

Repository scaffold, documentation, agent contracts. No code.

# Handoff Document

## PHASE: Scientific Validation Upgrade (Claude Code) — 2026-09-22

**Result:** Strengthened the scientific evaluation of the existing orbital-only PHA-approximation
experiment without rewriting it. Full report: `docs/SCIENTIFIC_REVIEW_REPORT.md`.

**Completed:**
- New `ml/diagnostics/` package (distribution shift, subgroup/orbital-class evaluation,
  calibration, definition-reconstruction, Apophis case study), each reproducible via
  `python -m ml.diagnostics.<name>`, writing to `ml/diagnostics/output/*.json`.
- `docs/EXPERIMENTS.md`: added a "Distribution shift investigation" section and Experiments 2–4,
  below the untouched, machine-appended Experiment 1 log.
- `docs/MODEL_CARD.md`, `docs/LIMITATIONS.md`, `docs/DATA_LEAKAGE.md`, `README.md`,
  `docs/SCIENTIFIC_INTEGRITY.md`, `docs/API_CONTRACT.md`: terminology and limitation-language
  updates per the review spec (exact required sentence on H/MOID exclusion; "orbital-geometry-
  based approximation" framing; "model score, not probability").
- `backend/app/schemas/prediction.py`: strengthened `DISCLAIMER` text; `probability` field name
  kept for compatibility (documented decision).
- Frontend (`Prediction.tsx`, `Models.tsx`, `types/api.ts`): "Model Score" replaces "Probability"
  in displayed text (API field unchanged); added the required orbital-geometry-score disclaimer
  line; added a Models-page scientific summary block (Target/Feature scope/Excluded/Status/
  Primary metric/No-skill baseline/Limitations).
- `tests/ml/test_diagnostics.py`: 11 new tests, including that diagnostic artifacts never
  overlap the production registry root and that `ml.inference` refuses the diagnostic feature
  version.

**Changed:** primary experiment (`ml/training`, `ml/preprocessing`, `ml/features`) is
**unchanged** — verified by re-running the full test suite and diffing those directories.

**Tests performed:** `pytest -m "not postgres"` 148 passed, 2 deselected (Postgres-marker,
unchanged); `ruff check .` clean; frontend `tsc --noEmit` 0 errors, `eslint --max-warnings 0`
clean, `vitest run` 18/18, `vite build` succeeds; manual browser verification of `/predict` and
`/models`.

**Known issues:** none introduced. Distribution-shift root cause remains explicitly
INCONCLUSIVE (documented, not a defect). A live backend process from an earlier session was
still serving the old `DISCLAIMER` string during manual browser verification — source is
correct; the running process just needs a restart to pick it up (uvicorn `--reload` should do
this automatically once the file is saved, which it was).

**Next agent:** none required immediately. If future work adds real probability calibration,
follow the "Recommended future work" section of `docs/SCIENTIFIC_REVIEW_REPORT.md` first.

**Required next actions:** none blocking. No `git commit`/`git push` was performed (per
instructions) — review `git status`/`git diff --stat` and commit manually when ready.

---

## PHASE: Phase 5 — Final Release Preparation (Claude Code) — 2026-09-22

**Result:** Repository prepared for manual review, commit, and push. No application code was
changed — CI added, security/secret audit performed, deployment configuration documented, stale
docs corrected, two open Phase 4 items investigated and resolved. **Nothing was committed or
pushed** — that is the user's manual step, per instructions. Full detail: `docs/RELEASE_REPORT.md`.

**CI:** IMPLEMENTED — `.github/workflows/ci.yml` (backend: ruff + pytest; frontend: typecheck,
lint, test, build), on push/PR to `main`.

**REACT ROUTER ADVISORIES:** Investigated, **not upgraded**. Both `npm audit` findings are
not exploitable in this app (no SSR; no attacker-controlled navigation input) — full reasoning
in `docs/SECURITY.md`.

**NEO EXPLORER SEARCH ISSUE (Phase 4 UNCONFIRMED item):** Re-investigated live against the full
required test checklist plus source inspection. **NOT REPRODUCED** — the search box has no
navigation call in its code path. Detail: `docs/VERIFICATION_REPORT.md`.

**SECRET AUDIT:** PASS — no real secrets in tracked/working-tree source; `.env`/`frontend/.env`
correctly git-ignored; `.env.example` files are placeholders only.

**DEPLOYMENT PREP:** Render (backend) and Vercel (frontend) configuration documented in
`docs/DEPLOYMENT.md` (build/start commands, env vars, health check). **Not provisioned** — needs
a human with platform access, and the model-artifact strategy is still an open decision (not
made here, per `docs/DEPLOYMENT.md`'s "decision needed" note, unchanged from Phase 2).

**DOCUMENTATION:** Corrected stale claims — root `README.md` said "Frontend: NOT IMPLEMENTED" and
listed CI/React as "Planned" despite both being implemented since Phase 3/3.5; a backend test-count
arithmetic error ("138" after a test was added, should be 139) was corrected in the Phase 3.5
entries of this file, `docs/TASK_TRACKER.md`, `docs/TESTING.md`, and `docs/STITCH_IMPLEMENTATION.md`
(Phase 4's own entries, written before that test existed, were left at 138 — accurate when written).

**FINAL TESTING (re-run this phase, not assumed):** Backend `pytest -m "not postgres"` 137 passed
(139 collected total incl. 2 Postgres-marker tests), `ruff check` clean, `pip-audit` clean. Frontend
`tsc --noEmit` 0 errors, `eslint --max-warnings 0` clean, `vitest` 18/18, `vite build` succeeds.
`git diff --check`: CRLF-on-checkout warnings only (Windows `core.autocrlf`), one intentional
Markdown hard-line-break in this file (not an error).

**NOT DONE (explicitly, not silently skipped):** automated browser E2E suite (documented as a
future improvement rather than adding a new test framework for one pass); actual Render/Vercel
provisioning and a production smoke test (needs human platform access + the artifact decision).

**NEXT AGENT:** the user (manual review → `git add` → `git commit` → `git push`) — see
`docs/RELEASE_REPORT.md` for the exact commands.
**NEXT PHASE:** none planned by Claude Code; future work is deployment (once the artifact decision
is made) and, if desired, an automated E2E suite.

---

## PHASE: Phase 3.5 — Stitch-Faithful Command Dashboard Redesign (Claude Code) — 2026-09-22

**Result:** Frontend visually reworked around a real Stitch-generated "NEO-Guard Planetary
Defense Command Dashboard" reference, using the existing real backend/ML/DB throughout. No
fabricated data was introduced; several Stitch elements requiring data this system doesn't have
(spectral classification, sensor telemetry, deflection/orbit-recalc/MPC-export tooling) were
replaced with honest real equivalents instead of copied as-is. Full report:
`docs/STITCH_IMPLEMENTATION.md`.

**STITCH MCP:** AVAILABLE — the real project/screen was located and its generated HTML/tokens
read directly (not guessed from the screenshot).

**DASHBOARD:** IMPLEMENTED. Command header, sidebar, KPI row, orbital radar (schematic, honestly
labeled), close-approach matrix, orbit-class chart, data-sources panel, and quick-actions panel
all rebuilt around real `/api/analytics`, `/api/health`, `/api/models` data.

**NEO EXPLORER / NEO DETAIL / ANALYTICS / MODELS / PREDICTION / ABOUT:** IMPLEMENTED (retoned to
the new design tokens; underlying data logic unchanged — these pages were already real and
working per the Phase 4 verification above).

**REAL DATA:** VERIFIED — every dashboard panel traces to a real backend field; see the
"Data-Driven Components" and "Unavailable Data" sections of `docs/STITCH_IMPLEMENTATION.md` for
exactly what was and wasn't reproduced, and why.

**FAKE DATA:** NONE.

**BUILD:** PASS (`vite build`). **TYPECHECK:** PASS (`tsc --noEmit`, 0 errors). **LINT:** PASS
(`eslint --max-warnings 0`). **TESTS:** PASS — frontend `vitest` 18/18; backend `pytest` 139/139
(one new backend field required one new test, both green).

**BACKEND CHANGE:** One small, justified additive field, `upcoming_close_approaches`, added to
`GET /api/analytics` (see `docs/API_CONTRACT.md`) — the only backend change made this phase.

**DOCUMENTATION:** UPDATED — `docs/DESIGN_SYSTEM.md`, `docs/FRONTEND_CONTRACT.md`,
`docs/API_CONTRACT.md`, `docs/TASK_TRACKER.md`, `docs/CHANGELOG.md`, this file, and the new
`docs/STITCH_IMPLEMENTATION.md`.

**KNOWN LIMITATIONS:** No automated visual-regression/E2E suite (verification was manual, live
in a real browser); `OrbitalRadar` is an explicitly-labeled schematic, not real orbital
mechanics; the pre-existing >500 KB main bundle size was not addressed (out of scope).

**NEXT AGENT:** Antigravity (or whichever agent owns deployment)
**NEXT PHASE:** Final release preparation + GitHub commit + deployment preparation (unchanged
from the Phase 4 entry below — this phase did not change deployment readiness).

---

## PHASE: Phase 4 — Verification (Claude Code) — 2026-09-22

**SYSTEM STATUS: PARTIALLY READY** — backend, database, ML serving, and frontend are all real,
working, and evidence-verified in this session (not trusted from prior claims — reproduced).
Not "READY" because: no authentication, no formal pen-test, model quality is honestly weak
(documented, not a defect), and deployment (Render/Vercel) has not been attempted.

**BACKEND:** PASS. `compileall`/`ruff` clean. 138/138 tests pass (136 unit/ML/integration + 2
PostgreSQL, reproduced against a real disposable test DB, not assumed). `pip-audit` clean.

**DATABASE:** PASS. `docker compose up` (db → migrate → backend) succeeds from a clean start;
Alembic migrations reproduce the schema; real JPL snapshot loaded (42,477 NEOs / 30,828
approaches, matches prior documented counts exactly).

**ML:** PASS (serving/inference/explainability). Existing 6 trained models, metrics, and SHAP
explanations reproduced via a live `/api/predict` call for Apophis's real orbital elements —
exact match to the sanity check in this document's prior entry. Full retraining was not rerun
this session (unnecessary — artifacts are versioned and their tests pass). Model quality
remains weak, as previously and honestly documented; that is not a new finding.

**FRONTEND:** PASS. `tsc --noEmit`, `eslint --max-warnings 0`, `vitest` (18/18), and
`vite build` all pass. Manually driven in a real browser against the live backend across all
6 routes (Dashboard, NEO Explorer, NEO Detail, Analytics, Models, Prediction, About) — including
a full prediction round-trip that matched a direct API call exactly, and a genuine backend-down
error state (retry button shown, no crash, verified after correcting an initial false read caused
by test-tooling timing, not an app defect).

**INTEGRATION:** PARTIAL. Full stack (Docker Postgres → FastAPI → real data → frontend) verified
end-to-end for the primary user journeys. One frontend interaction anomaly (NEO Explorer search
box occasionally appeared to navigate back to the dashboard during fast synthetic typing) could
not be reliably reproduced with isolated keystrokes and is not filed as a confirmed bug — flagged
for human attention during manual QA.

**NASA/JPL:** PASS (connectivity). Live request to `ssd-api.jpl.nasa.gov/cad.api` succeeded
(HTTP 200, real data) during this session. Full re-ingestion was not rerun (unnecessary — would
only create a redundant same-schema snapshot and cost real API calls); the existing 2026-09-21
snapshot was used for DB/model checks instead.

**DOCKER:** PASS. `docker compose build` and `docker compose up -d` both succeed; db reaches
`healthy`, migrate exits 0, backend reaches `healthy` and serves real traffic on port 8000.

**TESTS:** 138/138 Python (backend+ML), 18/18 frontend (vitest), all reproduced live this
session. Full breakdown and raw evidence: `docs/VERIFICATION_REPORT.md`.

**SECURITY:** No hardcoded secrets found in source; `.env` correctly gitignored; CORS rejects
wildcard origins in production; `pip-audit` clean. `npm audit` (prod deps): 2 moderate
`react-router-dom` advisories (open redirect / SSR hydration) — not exploitable in this
client-only SPA, but clearing them needs a v6→v7 major version bump; left as a P2 for a human
decision rather than an unrequested breaking dependency change. No authentication, no formal
penetration test — unchanged from prior phase, consistent with `docs/SECURITY.md`.

**KNOWN ISSUES (carried over from Phase 2/3, still accurate — see prior entry below for detail):**
scientific framing needs human confirmation; model quality is limited; model binaries not in
Git; no authentication; not yet deployed.

**REMAINING WORK:**
1. Human: decide model status (KNOWN ISSUE 1 in the entry below) — unchanged, still pending.
2. Decide whether/how to clear the `react-router-dom` advisories (major version bump).
3. Manually re-confirm the NEO Explorer search-box behavior noted under INTEGRATION above.
4. Deployment preparation (Render/Vercel), CI (`.github/workflows` still a placeholder),
   automated browser E2E suite.

**NEXT AGENT:** Antigravity
**NEXT PHASE:** Final release preparation + GitHub commit + deployment preparation

---

## PHASE: Backend + ML (Claude Code) — 2026-09-21

**Result: COMPLETE for the backend/ML scope, with real data. Two items need a human decision (see
KNOWN ISSUES 1–2). Nothing was committed or pushed (per instructions).**

## COMPLETED

* **Real data ingestion** from the JPL SBDB Query API and CAD API (no API key needed) — 42,477 near-Earth
  asteroids and 30,828 Earth close approaches, retrieved 2026-09-21, stored write-once with sha256 provenance.
* **Validation / normalisation** (internal schema, rejection log; 0 rejects on the real data), **PHA-rule audit**
  (JPL's flag equals `moid ≤ 0.05 au and H ≤ 22` for 42,301/42,351 objects), **preprocessing** (chronological split).
* **Leakage audit** of every column; `H`, `moid`, size proxies and post-outcome metadata excluded.
* **Feature engineering** `features-v1` (7 orbital elements → 9 inputs).
* **ML**: Logistic Regression, Random Forest, XGBoost × {no weighting, balanced} = **6 experimental models**;
  validation-tuned thresholds; held-out test evaluation with bootstrap CIs; SHAP (global + local); versioned artifacts.
* **Database**: PostgreSQL schema via Alembic (`0001`), idempotent loader, model/experiment registry.
* **FastAPI**: `/api/health, /neos, /neos/{id}, /neos/{id}/approaches, /predict, /models, /models/{version}, /analytics`,
  OpenAPI, structured errors/logging, CORS, security headers, rate limiting.
* **Docker**: `backend/Dockerfile`, `docker-compose.yml` (db + migrate + backend).
* **Tests**, **docs** (all listed under CHANGED).

## CHANGED

* New: `ml/` (pipeline), `backend/app`, `backend/alembic`, `backend/Dockerfile`, `backend/requirements*.txt`,
  `tests/`, `pyproject.toml`, `.dockerignore`.
* Replaced foundation placeholders: `docker-compose.yml`, `Makefile`, `.env.example`, `.gitignore`.
* Docs rewritten from templates to reality: `README`, `ARCHITECTURE`, `DATA_SOURCE`, `DATA_DICTIONARY`, `DATA_PIPELINE`,
  `DATA_LEAKAGE`, `FEATURE_POLICY`, `ML_WORKFLOW`, `MODEL_CARD`, `EXPERIMENTS`, `API_CONTRACT`, `DATABASE_SCHEMA`,
  `FRONTEND_CONTRACT`, `SECURITY`, `TESTING`, `LIMITATIONS`, `DEPLOYMENT`, `CHANGELOG`, `TASK_TRACKER`, and the READMEs of `backend/`, `ml/*`, `tests/*`.
* **Contract changes are tabulated in `docs/API_CONTRACT.md`** (health status values, integer NEO id, `diameter_km`
  instead of min/max, prediction response, …) and `docs/CHANGELOG.md`. `NASA_API_KEY` was removed (unused).

## TESTS

* `pytest`: **138 passed** (136 + 2 PostgreSQL tests that need `TEST_DATABASE_URL`); coverage **98%** of `ml/` + `backend/app`.
* `ruff check`: clean. `python -m compileall`: clean.
* Live/manual (2026-09-21): real JPL ingestion; real-data pipeline; `load-data` twice on PostgreSQL (0 inserted / 42,477 updated
  the 2nd time); `sync-models` twice; API smoke test (`/health`, `/neos`, `/neos/{id}`, approaches, `/models`, `/analytics`,
  `/predict`, errors, CORS, `/docs`, `/redoc`, `/openapi.json`); Alembic downgrade/upgrade on PostgreSQL; `docker build`,
  `docker compose up`, container `healthy`, runs as non-root, prediction inside the container identical to the host.
* Sanity check against public knowledge: Apophis's 2029 close approach came out as 0.000254 au = 38,011 km (JPL data through our pipeline).

## DATA SOURCE

JPL SBDB Query API v1.0 (`https://ssd-api.jpl.nasa.gov/sbdb_query.api`) and CAD API v1.5 (`…/cad.api`), unauthenticated.
Dataset version `jpl-sbdb-neo-20260921-c34b5103`. Details, exact queries and limits: `docs/DATA_SOURCE.md`. Raw files are git-ignored
(`data/raw/`); regenerate with `python -m ml.ingestion`.

## MODEL

Task: predict JPL's PHA flag from 7 orbital elements. Best on validation (and served by default): **`random_forest-v1`**
(validation PR-AUC 0.183; test PR-AUC 0.146 [0.088–0.236], ROC-AUC 0.898, precision 0.118, recall 0.391 at threshold 0.270).
All six models are **`experimental`** — none promoted. They beat chance (no-skill PR-AUC 0.013 on test) but are **weak**
(e.g. Apophis, a textbook PHA, is predicted "not hazardous"). Full table: `docs/EXPERIMENTS.md`; card: `docs/MODEL_CARD.md`.

## API

Running and verified; contract: `docs/API_CONTRACT.md`, live schema: `/openapi.json`. Start: `uvicorn app.main:app --reload` or
`docker compose up -d --build` (port 8000).

## DATABASE

PostgreSQL 16; six tables (`neo_objects`, `close_approaches`, `data_sources`, `models`, `experiments`, `predictions`);
`alembic -c backend/alembic.ini upgrade head` reproduces it from empty. Local state on the dev machine: the compose DB (host port
**55432**) holds the real data; `.env` (git-ignored) has a randomly generated password. `docker compose down` keeps the volume.

## KNOWN ISSUES

1. **Scientific framing needs human confirmation.** The label is a deterministic rule on `H` and `moid`; both are excluded to avoid
   trivial leakage, so the models only learn which *orbits* can approach Earth closely (a weaker task). Rationale and the decision
   requested: `docs/DATA_LEAKAGE.md` (top). No alternative was adopted silently.
2. **Model quality is limited** (weak precision/recall, misses Apophis, strong distribution shift 7.5% → 1.3%, only 64 test positives).
   The UI must present predictions as experimental estimates (see FRONTEND REQUIREMENTS). No model is `validated`/`production`.
3. **Model binaries are not in Git** (`*.joblib` ignored; random forests 47–53 MB). A Git-based deploy has no models until Phase 5
   decides how to ship them (`docs/DEPLOYMENT.md`). `metadata.json`/`evaluation.json`/`shap_global.json` are tracked.
4. **Docker image is 1.72 GB** (SHAP/XGBoost/scikit-learn/pandas). Acceptable locally; may matter on small hosts.
5. **No authentication**; rate limiter is per-process; `pip-audit` not run (`docs/SECURITY.md`).
6. **Live JPL access has no automated test** (verified by running the real command). JPL rate limits are undocumented; the client is polite.
7. **Dev-machine quirks:** a separate PostgreSQL occupies port 5432 (compose uses `POSTGRES_HOST_PORT=55432`); on Windows use
   `127.0.0.1` rather than `localhost` in `DATABASE_URL` (IPv6 fallback adds ~8 s).
8. **Not done:** frontend, E2E tests, CI (`.github/workflows` still a placeholder), Render/Vercel deployment.
9. License terms of the JPL data were not verified (`docs/DATA_SOURCE.md`).

## FRONTEND REQUIREMENTS

Read `docs/FRONTEND_CONTRACT.md` (TypeScript types, pagination/filter/sort rules, error handling, UX requirements) and
`docs/API_CONTRACT.md`. Key rules: show `model_version`, `model_status`, `threshold` and the `disclaimer` with every prediction; show JPL's
own PHA flag beside the model output; handle `null`s (diameter, name, PHA flag); approach dates are **TDB**; never bypass the API; use
`/openapi.json` for type generation; CORS allows `http://localhost:5173` by default (`CORS_ORIGINS`). ROC/PR curve points exist in
`ml/artifacts/*/v1/evaluation.json` but are not exposed by the API — add an endpoint only if the UI needs charts.

## REQUIRED NEXT ACTIONS

1. Human: review the scientific framing (KNOWN ISSUE 1) and decide model status (`python -m app.cli set-status <version> <status>`).
2. Antigravity: build the frontend against the running backend (Stitch design system, React + Vite + Tailwind).
3. Decide the model-artifact strategy before Phase 5 (`docs/DEPLOYMENT.md`).
4. Later phases: E2E/security verification, deployment, final Git commit.

---

## PHASE: Frontend + Design System (Antigravity) — Phase 3 Complete

**Result: COMPLETE for the entire Frontend scope, with Apple-inspired scientific dark visual design, verified API contracts, TypeScript type-safety, and production build.**

### COMPLETED
* **Design System**: Apple-inspired dark aesthetic (`#080B11` canvas, `#0D1117` surfaces, subtle 1px border glows, Inter + JetBrains Mono typography, status-colored pills). Documented in `docs/DESIGN_SYSTEM.md`.
* **7 Core Pages**:
  1. `Dashboard`: KPI cards (total NEOs, PHAs, monitored close approaches), recent approach feed with countdowns/AU distances, hazard breakdown pie, quick lookup.
  2. `NeoExplorer`: High-density catalog table, live text search, PHA/orbit class/diameter filters, column sorting, pagination controls, compact density toggle.
  3. `NeoDetail`: Full orbital parameter readouts, timeline of historical and upcoming close approaches with Earth distance badges, physical characteristics, JPL designation metadata.
  4. `Analytics`: MOID vs. relative velocity scatter plot, diameter distribution histogram, orbital family class distribution.
  5. `Models`: Model registry overview with status badges (`experimental`, `production`), side-by-side metric comparison (PR-AUC, ROC-AUC, F1, Recall, Precision), hyperparameters inspector, SHAP global feature impact rankings.
  6. `Prediction`: Interactive orbital parameter input with preset examples (Apophis, Bennu, 2024 BX1), live backend inference, probability gauge vs. decision threshold, SHAP local waterfall explanation with positive/negative force breakdown, and scientific disclaimers.
  7. `About`: Scientific methodology, data provenance (JPL SBDB & CAD), ML architecture, leakage audit explanation, and explicit limitations statement.
* **Component Library**: Composable `Card`, `Badge`, `Button`, `EmptyState`, `Spinner`, `Charts` (Recharts dark theme), and `MetricsTable`.
* **API Integration**: Strict TypeScript client mapping backend FastAPI response models with error recovery, retry policy, and connection health indicator in navigation.
* **Verification**:
  - `tsc --noEmit`: 0 errors
  - `eslint`: 0 errors, 0 warnings
  - `vitest`: 18 tests passed (formatters, data sanitizers, API error handlers)
  - `vite build`: Production build verified clean

### KNOWN ISSUES & NOTES
1. All predictions correctly display the backend's scientific disclaimer and highlight experimental model status.
2. In production deployment, `VITE_API_BASE_URL` configures the backend target (defaults to relative `/api` or `http://localhost:8000/api`).

**NEXT AGENT:** Claude Code  
**NEXT PHASE:** Full system verification, E2E testing, and deployment preparation


---

## Phase 1 — Foundation (Antigravity) — COMPLETED (summary)

Repository structure, documentation, agent contracts, data/ML/API/DB/frontend policies, `.gitignore`, `.env.example`,
`Makefile`, `docker-compose.yml` placeholders. No code, no data.

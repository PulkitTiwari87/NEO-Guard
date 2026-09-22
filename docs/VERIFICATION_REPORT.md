# NEO-Guard Phase 4 Verification

Status: COMPLETE
Date: 2026-09-22
Verifier: Claude Code
Environment: Windows 11, Python 3.12.6 (.venv), Node v22.12.0/npm 11.19.0, Docker Desktop 29.7.2 / Compose v5.5.1, live internet access confirmed

Backend: PASS
Frontend: PASS (one confirmed integration bug, see below)
Database: PASS
ML: PASS (quality caveats documented, not a defect)
NASA/JPL: PASS
Docker: PASS
Integration: PARTIAL (real bug found in NEO detail → Prediction handoff; documented, not fixed — frontend is out of scope for Claude Code per project CLAUDE.md)

## Method

Every item below was independently executed against a live system in this session — not
inferred from prior agents' claims. No previous PASS claim was accepted without reproduction.

## Component evidence

### Backend
- PASS — `python -m compileall backend ml tests`: clean, no errors.
- PASS — `ruff check ml backend tests`: "All checks passed!"
- PASS — `pytest -m "not postgres"`: **136 passed**, 0 failed.
- PASS — `pytest -m postgres` against a disposable `neoguard_test` database: **2 passed**.
  Combined: **138 passed**, matching the documented count in `docs/TESTING.md` — reproduced, not assumed.
- PASS — `pip-audit`: "No known vulnerabilities found" (Python dependencies).
- PASS — FastAPI app starts cleanly in Docker (`uvicorn` log: "Application startup complete").

### Database
- PASS — `docker compose up` (db → migrate → backend): all three containers reached
  healthy/exit-0 state. `neoguard-migrate-1` exited 0 (alembic upgrade head succeeded).
- PASS — `GET /api/health` returns `{"status":"ok","database":"ok",...}` — a genuine DB
  round-trip, not a static value (verified by stopping the backend and observing connection
  errors instead of a false "ok").
- PASS — `python -m app.cli load-data`: loaded the real JPL snapshot — 42,477 NEOs, 30,828
  close approaches (matches `docs/HANDOFF.md`'s documented counts exactly).
- PASS — `python -m app.cli sync-models`: registered 6 model versions.
- PASS — Postgres-marked tests exercise Alembic upgrade/downgrade on a real PostgreSQL instance.

### ML
- PASS — 6 trained model artifacts present under `ml/artifacts/` (logistic_regression,
  logistic_regression_balanced, random_forest, random_forest_balanced, xgboost, xgboost_balanced),
  each with real `metadata.json`/`evaluation.json`/`shap_global.json`.
- PASS — `GET /api/models` returns real metrics with bootstrap CIs (e.g. random_forest-v1: test
  PR-AUC 0.146, ROC-AUC 0.898) — matching `docs/EXPERIMENTS.md`/`docs/HANDOFF.md` exactly.
- PASS — `POST /api/predict` with Apophis's real orbital elements returns `probability: 0.1763`,
  `label: not_potentially_hazardous`, model `random_forest-v1`, threshold `0.270`, and a 9-feature
  SHAP breakdown that sums consistently with the base value — **exactly reproducing** the specific
  sanity check recorded in `docs/HANDOFF.md`.
- NOT RE-VERIFIED — full training/evaluation pipeline was not rerun from scratch this session
  (would take significant time and does not change already-versioned artifacts); existing
  artifacts, metrics, and the leakage-audit tests (`tests/ml/test_leakage.py`) were confirmed to
  pass instead. Model quality is honestly weak per existing docs — that is a documented, correctly
  disclosed limitation, not a fabrication.

### NASA/JPL
- PASS — Live connectivity check against `https://ssd-api.jpl.nasa.gov/cad.api` performed during
  this session: HTTP 200, real data returned. Live access is currently available.
- Full re-ingestion (`python -m ml.ingestion`) was **not** rerun in this session (would create a
  new dated raw snapshot and take significant time against a real external API); the existing
  2026-09-21 snapshot was used for DB load/model checks instead. Connectivity itself is proven.

### Docker
- PASS — `docker compose build`: both `backend` and `migrate` images built successfully.
- PASS — `docker compose up -d`: db (healthy) → migrate (exit 0) → backend (healthy).
- PASS — Backend container serves real traffic on port 8000 identical to the documented contract.

### API contract
- PASS — All 8 documented endpoints present in `/openapi.json` and match `docs/API_CONTRACT.md`
  exactly: `/api/health`, `/api/neos`, `/api/neos/{id}`, `/api/neos/{id}/approaches`,
  `/api/predict`, `/api/models`, `/api/models/{version}`, `/api/analytics`.
- PASS — `/docs` and `/redoc` both return HTTP 200.
- PASS — Error handling: unknown NEO id → 404; malformed predict body → 422 with field-level
  detail (not a fabricated generic error).
- PASS — CORS: preflight from `http://localhost:5173` allowed; security headers present
  (`x-content-type-options: nosniff`, `x-frame-options: DENY`).

### Frontend
- PASS — `npm ci`: clean install (391 packages).
- PASS — `npm run typecheck` (`tsc --noEmit`): 0 errors.
- PASS — `npm run lint` (ESLint, `--max-warnings 0`): 0 errors/warnings.
- PASS — `npx vitest run`: **18 passed** (matches documented count).
- PASS — `npm run build`: production build succeeds (703 KB main bundle, uncompressed — a
  non-blocking P3 performance note, no code-splitting yet).
- PASS — Dev server started and driven live in a real browser against the live backend:
  Dashboard, NEO Explorer (search/filter/pagination), NEO Detail (Apophis — orbital elements and
  both real close approaches rendered correctly, matching the API), Analytics (population,
  hazard/orbit-class charts, physical-property stats all real), Models (all 6 real model cards),
  Prediction (full round-trip: form → `/api/predict` → SHAP waterfall, result matched a direct
  curl call to the same endpoint exactly: 17.6% probability, 27.0% threshold, `random_forest-v1`).
- PASS — Error handling: stopping the backend container produces a real, user-facing
  "Unable to load data" panel with a Retry button on both the Dashboard and NEO Explorer (verified
  after correcting an initial false read caused by an async-timing artifact in the test tooling,
  not an app bug).
- P3 (non-blocking) — `npm audit --omit=dev`: 2 moderate vulnerabilities in `react-router-dom`
  (open-redirect / SSR-hydration advisories). Not exploitable here (this is a client-only SPA,
  no SSR), but a major-version bump (v6→v7) would be needed to clear it — left for a human/PM
  decision since it's a breaking change, not a "smallest diff" fix.
- UNCONFIRMED (Phase 4) — a full-string type into the NEO Explorer search box ("apophis") once appeared to
  bounce navigation back to the Dashboard. Isolated single-keystroke retests (`z`, `h`, `a`) did
  not reproduce it, and search/filter/pagination worked correctly in every other check. Most
  likely an artifact of the browser-automation tool's fast synthetic typing racing React's
  controlled-input state, not a confirmed application defect. Flagged for a human to watch for
  during manual QA, not filed as a bug.
- **NOT REPRODUCED (Phase 5, 2026-09-22)** — re-investigated per the required checklist: normal
  typing, rapid typing, deletion/backspace burst, native Escape-to-clear, Enter (form submit),
  empty search results, special characters (`!@#$%^&*()`), and search combined with the hazard
  filter — none navigated away from `/neos`, confirmed via `window.location` after each step.
  Root cause ruled out by source inspection, not just retesting:
  `frontend/src/pages/NeoExplorer.tsx`'s search input has no `useNavigate`/`Link`/router call in
  its change handler at all — it is pure local `useState`, so the page's own search box cannot
  cause navigation through application code, to the Dashboard or anywhere else. (The separate
  global search in `CommandHeader.tsx` does call `navigate('/neos?q=...')` on submit, by design —
  that is expected behavior, not the reported bug, and was not what Phase 4's note described.)
  Minor unrelated cosmetic note found during this pass: the NEO Explorer search input renders two
  overlapping clear ("×") icons — the browser's native `type="search"` clear control plus this
  app's own custom button. Not fixed here — cosmetic, unrelated to the reported navigation bug,
  out of scope for this phase.

### Security
- PASS — No hardcoded secrets found in tracked or working-tree source (`backend/`, `ml/`,
  `frontend/src/`, compose/Makefile) via pattern scan for key/secret/password/token assignments.
- PASS — `.env` (containing the local dev DB password) is correctly gitignored; not committed.
- PASS — CORS: wildcard origins explicitly rejected in production (`core/config.py`:
  `_no_wildcard_cors_in_production`), `allow_credentials=False`, methods/headers whitelisted.
- PASS — `pip-audit`: clean.
- P2 — `npm audit`: 2 moderate production vulnerabilities in `react-router-dom` (see above).
- Not done (documented limitation, consistent with `docs/SECURITY.md`): no authentication,
  no formal penetration test, per-process (not distributed) rate limiting.

## Bugs found this session

None requiring a code fix survived investigation. One suspected frontend routing bug
(search-box bounce-to-dashboard) could not be reliably reproduced and is recorded as
unconfirmed above rather than fixed blind. One initially-suspected "no error state" bug on
backend-down was disproven on a more careful retest (timing artifact in the verification
tooling, not the app) and is documented as a retraction above for transparency.

## Known limitations (carried over, still accurate)

Frontend/browser E2E automation beyond manual driving, load/performance testing, formal
penetration testing, and Render/Vercel deployment remain not done, consistent with
`docs/TESTING.md` and `docs/HANDOFF.md`.

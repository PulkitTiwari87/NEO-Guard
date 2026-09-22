# NEO-Guard — Task Tracker

## FOUNDATION
- [x] Repository structure
- [x] Documentation
- [x] Agent contracts
- [x] Data policy
- [x] ML policy
- [x] API contract
- [x] Database contract
- [x] Frontend contract

## BACKEND  (Phase 2 — Claude Code; each item implemented **and verified**, see `HANDOFF.md`)
- [x] Data ingestion (real JPL SBDB + CAD data fetched 2026-09-21)
- [x] Validation (0 rejected on real data; rejection paths tested)
- [x] Preprocessing (chronological split, de-duplication)
- [x] Feature engineering (`features-v1`, leakage audit)
- [x] Database (PostgreSQL + Alembic, real data loaded, idempotent)
- [x] ML training (LR / RF / XGBoost, 6 experimental models)
- [x] Evaluation (held-out test metrics, bootstrap CIs, `docs/EXPERIMENTS.md`)
- [x] Explainability (SHAP global + local, additivity verified)
- [x] FastAPI (all endpoints, OpenAPI, Docker image and compose stack verified)
- [x] Tests (unit, ML, integration, PostgreSQL migration)

Open backend follow-ups (not blocking): human review of the scientific framing
(`DATA_LEAKAGE.md`); model status promotion (all models are `experimental`); dependency audit.

## FRONTEND (Phase 3 — Antigravity; all 7 pages, design system, API integration, 18 tests)
- [x] Stitch design (Design system & tokens implemented)
- [x] React implementation (Vite + React 18 + TailwindCSS + React Query + Lucide)
- [x] Dashboard (Key metrics, recent approaches, hazard breakdown, quick search)
- [x] NEO explorer (Search, filters, pagination, sort, density toggle)
- [x] NEO details (Orbital elements, close approaches history, physical properties, risk badge)
- [x] Analytics (MOID vs velocity scatter, diameter distribution, orbit class breakdown)
- [x] Model dashboard (Registered models, metrics comparison, hyperparams, feature importance)
- [x] Prediction UI (Interactive 7-feature orbital input, presets, SHAP waterfall, confidence)

## FRONTEND REDESIGN (Phase 3.5 — Claude Code, 2026-09-22, after Phase 4 verification;
evidence in `docs/STITCH_IMPLEMENTATION.md`)
- [x] Stitch MCP inspected (real project/screen located and its generated HTML/tokens read)
- [x] Design tokens retoned to the Stitch aerospace HUD palette (`tailwind.config.js`, `index.css`)
- [x] Command header + sidebar rebuilt (real health/dataset state, fake DEFCON/LOG ENCOUNTER removed)
- [x] Dashboard rebuilt around real data (orbital radar, close-approach matrix, data sources,
      quick actions — all replacing Stitch's fabricated equivalents)
- [x] One small, documented backend addition (`upcoming_close_approaches` on `/api/analytics`)
      to power the above with real data; tested, documented in `API_CONTRACT.md`
- [x] NEO Explorer, NEO Detail, Analytics, Models, Prediction, About retoned and spot-verified live
- [x] Build/typecheck/lint/vitest all green after the retheme; backend suite re-run green (139/139)
- [ ] Automated visual-regression coverage for the new theme (verification was manual/live-browser)

## VERIFICATION (Phase 4 — Claude Code, 2026-09-22; evidence in `docs/VERIFICATION_REPORT.md`)
- [x] Unit tests (138 passed, reproduced this session: 136 unit/ML/integration + 2 PostgreSQL)
- [x] Integration tests (API ↔ DB ↔ model; PostgreSQL migration; reproduced against a real Docker stack)
- [x] Full-stack manual E2E (Docker db+migrate+backend, real data loaded, frontend driven live
      against it across all 6 routes, real prediction round-trip verified)
- [x] Docker (build + up verified: db healthy, migrate exit 0, backend healthy)
- [x] NASA/JPL live connectivity (confirmed working this session)
- [ ] Security verification (secrets scan, CORS, `pip-audit` clean this session; formal
      pen-test and authentication still not done — see `docs/SECURITY.md`)
- [ ] ML verification (independent scientific review still pending; internal leakage-audit and
      training/evaluation tests reproduced and pass)
- [ ] Automated browser E2E test suite (this phase drove the browser manually, not via a
      committed Playwright/Cypress suite)

## RELEASE PREP (Phase 5 — Claude Code, 2026-09-22; evidence in `docs/RELEASE_REPORT.md`)
- [x] React Router advisories investigated; not upgrading (decision documented, `docs/SECURITY.md`)
- [x] NEO Explorer search-box navigation issue re-investigated live (normal/rapid typing, paste-equivalent,
      deletion, empty search, special characters, search+filter, search+pagination) — **NOT REPRODUCED**;
      root cause ruled out by inspection: `NeoExplorer.tsx`'s search box has no `navigate()`/router call
      at all, so it cannot cause navigation by itself (`docs/VERIFICATION_REPORT.md`)
- [x] Minimal CI (`.github/workflows/ci.yml`): backend (`ruff`, `pytest -m "not postgres"`) + frontend
      (`typecheck`, `lint`, `test`, `build`)
- [x] Secret audit (`.env`/`.env.*` pattern scan; no real secrets in tracked files; `.env.example` /
      `frontend/.env.example` are placeholders only)
- [x] `.gitignore` verified (`.env`, `node_modules/`, `.venv/`, `__pycache__/`, `dist/`, `.pytest_cache/`, etc.)
- [x] README updated to reflect frontend + CI as implemented (was stale, still said "Frontend: NOT IMPLEMENTED")
- [x] Deployment docs: Render (backend) and Vercel (frontend) configuration documented — not provisioned
- [ ] Automated browser E2E suite — decided against for this phase (would add Playwright/Cypress, a new
      dependency, for one pre-release pass); documented as a future improvement, not built

## DEPLOYMENT
- [ ] Render (configuration documented in `docs/DEPLOYMENT.md`; not provisioned)
- [ ] Vercel (configuration documented in `docs/DEPLOYMENT.md`; not provisioned)
- [ ] Database (provider TBD)
- [x] Environment variables (documented in `docs/DEPLOYMENT.md` and `.env.example`)
- [ ] Production smoke test

# NEO-Guard Release Report

## Phase

5 — Final release preparation (manual GitHub push)

## Verification baseline

Phase 4 (`docs/VERIFICATION_REPORT.md`, 2026-09-22). Its evidence was reused where nothing in Phase 5
invalidated it (e.g. Docker/DB/NASA-JPL connectivity, model metrics). Anything Phase 5 re-checked or
changed is called out below rather than silently assumed.

## Phase 5 changes

No application/business logic was changed. Work this phase was: add CI, investigate two open Phase 4
items, run a security/secret audit, document Render/Vercel deployment configuration, and correct
stale documentation. Full diff-level detail: `docs/CHANGELOG.md` ("Phase 5" entry).

* **Added** `.github/workflows/ci.yml` (backend: `ruff check` + `pytest -m "not postgres"`; frontend:
  `npm ci`, `typecheck`, `lint`, `test`, `build`) and updated `.github/workflows/README.md` to match.
* **Investigated and resolved** the `react-router-dom` `npm audit` advisories (2 moderate) — decision:
  **not upgrading**, not exploitable in this client-only SPA. Reasoning in `docs/SECURITY.md`.
* **Investigated and resolved** the Phase 4 UNCONFIRMED "NEO Explorer search box bounces to
  Dashboard" note — **NOT REPRODUCED**, and ruled out at the source level (the search box has no
  navigation call in its code path). Detail in `docs/VERIFICATION_REPORT.md`.
* **Documented** Render (backend) and Vercel (frontend) deployment configuration in
  `docs/DEPLOYMENT.md` — not provisioned; the model-artifact strategy remains an explicit open
  human decision (unchanged from Phase 2/`docs/DEPLOYMENT.md`'s original "decision needed" note).
* **Corrected** stale documentation: root `README.md` claimed "Frontend: NOT IMPLEMENTED" and listed
  CI/React as "Planned" despite both being implemented and verified since Phase 3/3.5; a backend
  test-count arithmetic error ("138" after Phase 3.5 added a new test, should be 139) was corrected
  in the affected Phase 3.5 doc entries (Phase 4's own entries, written before that test existed,
  were correctly left at 138).

## Tests

Re-run this session (not assumed from prior phases):

| Suite | Result |
|---|---|
| `python -m ruff check ml backend tests` | All checks passed |
| `python -m compileall ml backend tests` | Clean |
| `pytest -m "not postgres"` | 137 passed |
| `pytest --collect-only` | 139 tests collected total (137 non-Postgres + 2 Postgres-marker) |
| `pip-audit` | No known vulnerabilities |
| `npm run typecheck` (frontend) | 0 errors |
| `npm run lint` (frontend) | 0 errors/warnings |
| `npm test` (frontend, vitest) | 18/18 passed |
| `npm run build` (frontend) | Succeeds (716.97 kB main bundle uncompressed — pre-existing, non-blocking) |
| `git diff --check` | CRLF-on-checkout warnings only (Windows `core.autocrlf`); one intentional Markdown hard-line-break in `docs/HANDOFF.md` — not a real issue |

The 2 Postgres-marker tests were not re-run against a live database this session (they were verified
against a real disposable Postgres instance in Phase 4, per `docs/VERIFICATION_REPORT.md`, and no
migration or DB-layer code changed since then).

## Security

* `pip-audit`: clean.
* `npm audit --omit=dev`: 2 moderate `react-router-dom` advisories, reviewed and not upgraded (see
  `docs/SECURITY.md` for the full reasoning and the exact `Link`/`navigate()` call sites checked).
* Secret scan: pattern search for `API_KEY|SECRET|PASSWORD|PRIVATE_KEY|DATABASE_URL|CREDENTIAL|TOKEN`
  assignments across tracked and working-tree source (`.py`, `.ts`/`.tsx`, `.js`/`.jsx`, `.yml`,
  `.json`, `.env*`) found no real secrets outside `.env`/`.env.example` themselves. The real local
  `.env` and `frontend/.env` files exist on disk but are correctly excluded by `.gitignore` (they do
  not appear in `git status`); `.env.example` and `frontend/.env.example` contain placeholders only.
* `.gitignore` verified to cover `.env`/`.env.*`, `node_modules/`, `.venv/`, `__pycache__/`/`*.pyc`,
  `dist/`/`build/`, `.pytest_cache/`/`.mypy_cache/`/`.ruff_cache/`, `*.log`, and model binaries
  (`ml/artifacts/**/*.joblib`).
* CORS, rate limiting, security headers, input validation, non-root container user: unchanged from
  Phase 4, re-confirmed by reading `backend/app/core/config.py` and `docs/SECURITY.md` — still
  environment-driven and production-safe (no hardcoded localhost-only CORS, no `*` allowed in
  `MODEL_ENV=production`).

## CI

Implemented this phase: `.github/workflows/ci.yml`. Not yet run on GitHub Actions (no push has
occurred); both jobs were validated locally by running their exact commands (ruff, pytest, npm
typecheck/lint/test/build — see Tests table above), which all passed.

## ML status

**EXPERIMENTAL** — unchanged. All six trained models remain `experimental`; none was promoted. No
new training or evaluation was run this phase (no reason to — no ML code changed). Model docs
(`docs/MODEL_CARD.md`, `docs/EXPERIMENTS.md`, `docs/LIMITATIONS.md`) already state this accurately
and were not altered.

## NASA/JPL

Not re-verified this phase (no ingestion code changed since Phase 4's confirmed live connectivity
check against `ssd-api.jpl.nasa.gov`). The locally running Docker stack was observed already healthy
with real 2026-09-21 JPL data loaded (42,477 NEOs / 30,828 approaches), consistent with prior phases.

## Stitch UI

Unchanged this phase — Phase 3.5's redesign (`docs/STITCH_IMPLEMENTATION.md`) stands; only its
backend-test-count claim was corrected for accuracy (138 → 139, see Phase 5 changes above).

## Deployment preparation

Render (backend) and Vercel (frontend) configuration is now documented in `docs/DEPLOYMENT.md`
(Docker/Dockerfile path, health check, port, env vars for Render; root dir, framework, build
command, output dir, `VITE_API_BASE_URL` for Vercel). **Not provisioned on either platform.** The
model-artifact strategy (how `*.joblib` files reach a Git-based deploy) remains an open decision for
a human — three options are listed in `docs/DEPLOYMENT.md`, none was chosen unilaterally.

## Known limitations

Unchanged from Phase 4 (`docs/LIMITATIONS.md`): weak model quality (documented, not a defect,
Apophis is missed), no authentication, per-process rate limiting, no formal penetration test, no
independent scientific/expert model review, single JPL data snapshot, discovery-bias in training
data. See `docs/LIMITATIONS.md` for the full, previously-verified list — nothing here changed.

## Known issues

* Model-artifact deployment strategy still undecided (blocks an actual Render deploy of
  `/api/predict`) — human decision required, `docs/DEPLOYMENT.md`.
* No automated browser E2E suite — documented as a future improvement rather than built this phase
  (would require adding a new test framework dependency for one release pass).
* Main frontend bundle is 716.97 kB uncompressed (202 kB gzip) — pre-existing, non-blocking, not
  addressed (no code-splitting yet).
* `react-router-dom` has 2 moderate `npm audit` advisories, deliberately not fixed — see Security
  above.

## Git status

Working tree is **DIRTY** — many modified docs (see `git status`), several new untracked files
(`.github/workflows/ci.yml` among them, plus the pre-existing untracked backend/frontend/ml source
from Phases 2–3.5 that was never committed). `git diff --check` shows only CRLF-on-checkout
warnings and one intentional Markdown hard-line-break — no real whitespace errors. Nothing was
staged, committed, or pushed by Claude Code this phase, per instructions.

## FINAL USER ACTION

Manual review → commit → push. See the handoff message in this session (or `docs/HANDOFF.md`'s
Phase 5 entry) for the exact commands: `git status`, `git diff --check`, review `git diff`,
`git add .`, `git status` again, `git commit -m "feat: complete NEO-Guard platform"`,
`git log -1 --oneline`, `git push origin main`.

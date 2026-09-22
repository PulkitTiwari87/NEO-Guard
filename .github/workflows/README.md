# GitHub Actions Workflows

**Status: IMPLEMENTED (CI only; no CD)**

`ci.yml` runs on every push/PR to `main`:

* **backend** — installs `backend/requirements-dev.txt`, `ruff check`, `pytest -m "not postgres"`
  (136 unit/ML/integration tests; the 2 PostgreSQL migration tests need a live database and are
  not run in CI — see `docs/TESTING.md`).
* **frontend** — `npm ci`, `tsc --noEmit`, `eslint --max-warnings 0`, `vitest run`, `vite build`.

Deployment (Render/Vercel) is manual for now; see `docs/DEPLOYMENT.md`.

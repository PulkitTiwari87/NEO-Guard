# Deployment

> **Status: NOT DEPLOYED — NOT VERIFIED on any hosting platform.** The backend runs locally and in
> Docker Compose (verified 2026-09-21, re-verified 2026-09-22). Render/Vercel configuration is now
> documented below (Phase 5) but has not been applied to an actual account, and the model-artifact
> question is still an open human decision. Do not claim deployment works until a production smoke
> test has passed.

## Target platforms

| Service | Platform | Status |
|---------|----------|--------|
| Frontend | Vercel | Configuration documented (below); not provisioned |
| Backend | Render | Configuration documented (below); not provisioned (image builds and runs locally/Docker) |
| Database | PostgreSQL provider (TBD) | NOT IMPLEMENTED |

## Backend (verified locally)

```
Build:     docker build -f backend/Dockerfile -t neoguard-backend .     # context = repo root (needs ml/)
Migrate:   alembic upgrade head                                          # cwd /app/backend in the image
Start:     uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
Runtime:   Python 3.12 (3.11+ supported), non-root user, HEALTHCHECK -> GET /api/health
```
Local stack: `docker compose up -d --build` starts `db` (PostgreSQL 16), runs `migrate` once, then `backend`
(port 8000, artifacts mounted read-only from `./ml/artifacts`). Data/model setup from the host:
`python -m app.cli load-data && python -m app.cli sync-models`.

## Database

Connection string via `DATABASE_URL` (plain `postgresql://…` is accepted). Schema is created **only** by
Alembic (`alembic upgrade head`), which is reproducible from an empty database. Data is loaded by
`python -m app.cli load-data` (idempotent) — the API never fetches from JPL at request time.

## Environment variables

See [`.env.example`](../.env.example). **`NASA_API_KEY` was removed** (JPL APIs need no key).

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | **Yes** | PostgreSQL connection string (no default) |
| `POSTGRES_PASSWORD` | compose only | Password of the compose `db` service; must match `DATABASE_URL` |
| `POSTGRES_HOST_PORT` | no | Host port of the compose DB (default 5432; use another if taken) |
| `MODEL_ENV` | no | `development` (default) \| `production` \| `test`; production forbids `CORS_ORIGINS=*` |
| `CORS_ORIGINS` | no | Comma-separated allowed origins (default `http://localhost:5173`) |
| `LOG_LEVEL` | no | Default `INFO` |
| `RATE_LIMIT_PER_MINUTE` | no | Per-client limit, default 120, `0` disables |
| `MODEL_DIR` | no | Artifact directory (default `ml/artifacts`) |
| `ACTIVE_MODEL_VERSION` | no | Pin the served model (default: best status, then validation PR-AUC) |
| `NEOGUARD_DATA_DIR` | no | Data pipeline root (default `data/`), used by `python -m ml.*` |

## Model artifacts — decision needed before deployment

`*.joblib` files are **git-ignored** (random forests are 47–53 MB; XGBoost ≈ 1 MB; logistic regression
≈ 8 KB). A Git-based deploy (e.g. Render) therefore ships no models, and `/api/predict` answers
`503 No trained model is available`. Options for Phase 5 (not chosen here): commit the small
XGBoost/LR artifacts with `git add -f`; train during the build (needs the data and network to JPL);
or attach a persistent disk / object storage for `MODEL_DIR`. Whatever is chosen, run
`python -m app.cli sync-models` after deployment and keep `feature_version` in sync with the code.

## Health check

`GET /api/health` → `200 {"status":"ok","database":"ok",…}`; `503` when the database is unreachable.
Use it as the platform health check (exempt from rate limiting).

## Render (backend) — configuration to use, not yet applied

| Setting | Value |
|---|---|
| Environment | Docker |
| Dockerfile path | `backend/Dockerfile` (build context = repository root — the image needs `ml/`) |
| Build command | none — Docker build only |
| Start command | none — uses the Dockerfile `CMD`, which runs `alembic upgrade head && python -m app.cli load-data && python -m app.cli sync-models` before `uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers` (Render's single web service has no separate one-off migrate step like `docker-compose.yml`'s `migrate` service, so these run — idempotently, from data already baked into the image — on every start) |
| Port | 8000 (`EXPOSE 8000` in the Dockerfile; Render's Docker runtime detects it) |
| Health check path | `/api/health` |
| Environment variables | see the table above — `DATABASE_URL`, `MODEL_ENV=production`, `CORS_ORIGINS=<vercel-url>` at minimum |

**Not applied yet** because the model-artifact question below is unresolved — a Render deploy today
would build and serve `/api/predict` with `503 No trained model is available` until artifacts are
provided.

## Vercel (frontend) — configuration to use, not yet applied

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Framework preset | Vite |
| Build command | `npm run build` |
| Output directory | `dist` |
| Environment variables | `VITE_API_BASE_URL=<deployed backend URL>` (see [`frontend/.env.example`](../frontend/.env.example)) |

Set the backend's `CORS_ORIGINS` to the deployed frontend origin (no wildcard in production). Never
hard-code the backend URL in frontend source — it must come from `VITE_API_BASE_URL`.

## Production checklist

See [`SECURITY.md`](SECURITY.md). Open: HTTPS (platform), auth decision, **model-artifact strategy
(human decision required — see above, not chosen by Claude Code)**, production smoke test after
Render/Vercel are actually provisioned. Dependency audit: done this session (`pip-audit` clean;
`npm audit` — see `SECURITY.md` for the `react-router-dom` decision).

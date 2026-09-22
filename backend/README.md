# Backend

FastAPI service (`app/`), PostgreSQL via SQLAlchemy/Alembic. **Status: IMPLEMENTED.** Contracts:
[`API_CONTRACT.md`](../docs/API_CONTRACT.md), [`DATABASE_SCHEMA.md`](../docs/DATABASE_SCHEMA.md).

## Run locally (repository root)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt
pip install -e . --no-deps                              # makes `app` and `ml` importable
cp .env.example .env                                    # set DATABASE_URL / POSTGRES_PASSWORD
docker compose up -d db                                 # PostgreSQL 16 (or use your own)
alembic -c backend/alembic.ini upgrade head            # create the schema (no manual tables)
python -m app.cli load-data                             # needs data/interim/ from `python -m ml.validation`
python -m app.cli sync-models                           # needs ml/artifacts/ from `python -m ml.training`
uvicorn app.main:app --reload                           # http://localhost:8000  (/docs, /redoc, /openapi.json)
```

Full stack in Docker: `docker compose up -d --build` (db + migrate + backend on :8000).
The data/ML steps that produce `data/` and `ml/artifacts/` are in [`DATA_PIPELINE.md`](../docs/DATA_PIPELINE.md).

## Layout

```
app/main.py            application factory (CORS, middleware, routers)
app/api/               routes_{health,neos,prediction,models,analytics}.py  (thin)
app/core/              config (env), logging (JSON), errors, security (headers, rate limit)
app/db/                models.py, database.py, loader.py, repositories/  (all SQL)
app/schemas/           pydantic request/response models (the API contract)
app/services/          prediction_service (model cache + SHAP), analytics_service
app/cli.py             python -m app.cli {load-data, sync-models, set-status}
alembic/               migrations (0001 = initial schema)
```

## Commands

| Command | Purpose |
|---|---|
| `python -m app.cli load-data` | Idempotent load of validated JPL data |
| `python -m app.cli sync-models` | Register artifacts/experiments (keeps human-set status) |
| `python -m app.cli set-status <version> <status>` | `experimental`/`validated`/`production`/`deprecated` |
| `pytest` | Whole suite (PostgreSQL tests need `TEST_DATABASE_URL`) |

Configuration is environment-only (see [`.env.example`](../.env.example)); `DATABASE_URL` is required.

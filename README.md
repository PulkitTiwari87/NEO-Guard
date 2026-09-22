# NEO‑Guard

**Explainable Machine Learning System for Near‑Earth Object (NEO) Classification and Close‑Approach Analysis**

## Status

**Backend + ML: IMPLEMENTED. Frontend: IMPLEMENTED. CI: IMPLEMENTED. Deployment: NOT DONE (Render/Vercel
not yet attempted).**
Real NASA/JPL data is ingested, validated, stored in PostgreSQL and served by a FastAPI API; six
experimental models were trained and evaluated; a React + Vite frontend consumes the API end to end.
See [`docs/HANDOFF.md`](docs/HANDOFF.md), [`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md)
and [`docs/RELEASE_REPORT.md`](docs/RELEASE_REPORT.md) for the full status.

## Architecture

```
NASA/JPL (SBDB, CAD) → ingestion → validation → preprocessing → features → training → evaluation → registry → FastAPI → React frontend
  [implemented]            [implemented all stages]                                          [implemented]
```

## What it does

* Ingests **42,477 near‑Earth asteroids** and **30,828 predicted Earth close approaches** from the JPL SBDB Query and
  CAD APIs (no API key needed) with immutable raw snapshots and provenance.
* Trains Logistic Regression, Random Forest and XGBoost to predict JPL's **PHA flag** from orbital elements only,
  under a leakage audit and a chronological split, with SHAP explanations.
* Serves NEO data, close approaches, analytics, model metadata and predictions through a documented REST API
  (`/docs`, `/openapi.json`).

## Results, honestly

The models beat chance but are **weak**: best on validation is `random_forest-v1` (test PR‑AUC 0.146 vs a 0.013 no‑skill
level, ROC‑AUC 0.898, precision 0.118, recall 0.391; only 64 positives in the test set). They cannot see the absolute magnitude
`H` (half of the PHA definition, excluded to avoid leakage) and they miss famous PHAs such as Apophis. All models are
`experimental`. Details: [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md), [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md),
[`docs/LIMITATIONS.md`](docs/LIMITATIONS.md). **This is not an impact‑prediction system.**

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt && pip install -e . --no-deps
cp .env.example .env                                        # set DATABASE_URL and POSTGRES_PASSWORD

# 1. data + models (real JPL data)
python -m ml.ingestion && python -m ml.validation && python -m ml.preprocessing
python -m ml.training && python -m ml.evaluation && python -m ml.explainability

# 2. database + API
docker compose up -d db
alembic -c backend/alembic.ini upgrade head
python -m app.cli load-data && python -m app.cli sync-models
uvicorn app.main:app --reload                               # http://localhost:8000/docs
```

Everything in Docker: `docker compose up -d --build` (db + migrations + backend). Tests: `pytest` (139 pass with a
PostgreSQL test DB). Commands are described in [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) and
[`backend/README.md`](backend/README.md).

```bash
# 3. frontend (needs the API running above)
cd frontend && npm install
cp .env.example .env                                        # VITE_API_BASE_URL, defaults to http://localhost:8000
npm run dev                                                  # http://localhost:5173
```

Frontend commands (typecheck/lint/test/build): [`frontend README`](frontend) and `package.json`. CI runs the same
checks on every push/PR: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Technology

Python 3.12 · FastAPI · Pydantic · SQLAlchemy · Alembic · PostgreSQL · httpx · scikit‑learn · XGBoost · SHAP · pytest · Docker.
React 18 · Vite · TypeScript · TailwindCSS · React Query · Recharts · Vitest (frontend). GitHub Actions (CI).
Planned: Vercel/Render (deployment).

## Scientific integrity

No fabricated data, metrics or claims; synthetic data exists only in tests and is labelled `SYNTHETIC / TEST DATA`.
See [`docs/SCIENTIFIC_INTEGRITY.md`](docs/SCIENTIFIC_INTEGRITY.md) and the open scientific question in
[`docs/DATA_LEAKAGE.md`](docs/DATA_LEAKAGE.md).

## Documentation

[Architecture](docs/ARCHITECTURE.md) · [Data source](docs/DATA_SOURCE.md) · [Data dictionary](docs/DATA_DICTIONARY.md) ·
[Pipeline](docs/DATA_PIPELINE.md) · [Leakage](docs/DATA_LEAKAGE.md) · [Features](docs/FEATURE_POLICY.md) ·
[ML workflow](docs/ML_WORKFLOW.md) · [Model card](docs/MODEL_CARD.md) · [Experiments](docs/EXPERIMENTS.md) ·
[API](docs/API_CONTRACT.md) · [Database](docs/DATABASE_SCHEMA.md) · [Frontend contract](docs/FRONTEND_CONTRACT.md) ·
[Security](docs/SECURITY.md) · [Testing](docs/TESTING.md) · [Deployment](docs/DEPLOYMENT.md) ·
[Limitations](docs/LIMITATIONS.md) · [Changelog](docs/CHANGELOG.md) · [Handoff](docs/HANDOFF.md)

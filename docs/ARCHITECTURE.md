# Architecture

> **Status: backend + ML IMPLEMENTED (2026-09-21); frontend PLANNED.**

## System architecture

```
NASA/JPL (SBDB Query API, CAD API)
        |  ml/ingestion            [IMPLEMENTED]  httpx client, retry/backoff, cache
        v
  Raw data  data/raw/             write-once snapshots + provenance
        |  ml/validation          [IMPLEMENTED]  schema, ranges, duplicates, rejections
        v
  Interim   data/interim/         validated, normalised (internal schema)
        |                 \
        |                  \-> app.cli load-data --> PostgreSQL (neo_objects, close_approaches, data_sources)
        |  ml/preprocessing       [IMPLEMENTED]  eligibility, de-dup, chronological split
        v
  Processed data/processed/       features + target + split manifest
        |  ml/features + ml/training   [IMPLEMENTED]  sklearn Pipeline, 3 algorithms x 2 weightings
        v
  Artifacts ml/artifacts/<name>/v<N>/   versioned model + metadata
        |  ml/evaluation, ml/explainability   [IMPLEMENTED]  test metrics, SHAP, EXPERIMENTS.md
        v
  Model registry (PostgreSQL `models`, `experiments`; status set by humans)   [IMPLEMENTED]
        |
        v
  FastAPI backend (backend/app)   [IMPLEMENTED]  /api/*  ->  ml.inference (predict + SHAP)
        |
        v
  Frontend (React)                [PLANNED — Phase 3]
```

## Components

| Component | Responsibility | Status |
|-----------|---------------|--------|
| Data Ingestion (`ml/ingestion`) | Fetch NEO orbits and close approaches from JPL; preserve raw responses | IMPLEMENTED |
| Validation (`ml/validation`) | Schema/quality checks, normalisation to the internal schema, rejection log | IMPLEMENTED |
| Preprocessing (`ml/preprocessing`) | ML dataset: eligibility, de-duplication, chronological split | IMPLEMENTED |
| Feature Engineering (`ml/features`) | Stateless features + leakage audit registry | IMPLEMENTED |
| ML Training (`ml/training`) | LR / RF / XGBoost pipelines, validation-tuned threshold, artifacts | IMPLEMENTED |
| Evaluation (`ml/evaluation`) | Metrics, curves, bootstrap CIs, experiment log | IMPLEMENTED |
| Explainability (`ml/explainability`) | SHAP global + local | IMPLEMENTED |
| Inference (`ml/inference`) | Load artifact, predict, explain | IMPLEMENTED |
| Model Registry | `models`/`experiments` tables + `ml/artifacts` (lightweight; statuses never automatic) | IMPLEMENTED |
| Backend (`backend/app`) | FastAPI routes → services/repositories → DB / `ml` | IMPLEMENTED |
| Database | PostgreSQL 16 via SQLAlchemy + Alembic | IMPLEMENTED |
| Frontend | React dashboard, explorer, prediction UI | PLANNED |
| Deployment | Vercel + Render | NOT IMPLEMENTED |

## Repository layout (implemented)

```
ml/                  data + ML pipeline (importable package `ml`; CLI: python -m ml.<stage>)
  ingestion/ validation/ preprocessing/ features/ training/ evaluation/ explainability/ inference/
  artifacts.py config.py artifacts/ (model binaries git-ignored)
backend/
  app/{main.py, api/, core/, db/, schemas/, services/, cli.py}
  alembic/  alembic.ini  requirements*.txt  Dockerfile
tests/{unit,ml,integration}  helpers.py (SYNTHETIC / TEST DATA)   conftest.py
docs/  data/{raw,interim,processed}  docker-compose.yml  pyproject.toml  Makefile
```

Layering in the backend: **routes** (validation, wiring) → **services** (`prediction_service`,
`analytics_service`) and **repositories** (`db/repositories`, all SQL) → ORM models. No business logic
in route handlers. The prediction service caches loaded models and never imports training code.
Design note: the foundation suggested `nasa_service.py` inside the backend; ingestion lives in
`ml/ingestion` instead because it is a batch pipeline stage, not a request-time concern (the API never
calls JPL at request time).

## Data flow

Raw data is immutable. All transformations produce new files in downstream directories.
`NASA/JPL --> data/raw/ --> data/interim/ --> data/processed/ --> ML pipeline`

## ML flow

`Processed data --> chronological split --> pipeline fit (train) --> threshold (validation) --> evaluation (test) --> artifact --> registry --> inference API`

## API flow

`Frontend --> Backend API --> PostgreSQL` and `--> ml.inference (model files)`; the frontend must not
access the database directly.

## Database flow

`Ingestion --> neo_objects, close_approaches, data_sources`; `ML --> models, experiments`; `API --> predictions` (only for known NEOs).

## Development architecture

Local: `docker compose up` (db + one-off migrate + backend) or a venv with `pip install -e . --no-deps`;
CI: GitHub Actions (not implemented).

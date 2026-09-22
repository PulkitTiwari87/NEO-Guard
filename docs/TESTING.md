# Testing Strategy

> **Status: IMPLEMENTED.** Last full run (2026-09-22, Phase 5): **139 passed** with a PostgreSQL test
> database (137 passed + 2 skipped without one); `ruff check` clean; `python -m compileall` clean.

## Running

```bash
pip install -r backend/requirements-dev.txt && pip install -e . --no-deps
pytest                                   # everything (PostgreSQL tests skip without TEST_DATABASE_URL)
pytest tests/unit | tests/ml | tests/integration
pytest --cov=ml --cov=app --cov-report=term
ruff check ml backend tests
```

PostgreSQL tests (`tests/integration/test_postgres.py`, marker `postgres`) need a **disposable**
database — they run `alembic downgrade base` and drop its tables. Never point `TEST_DATABASE_URL` at
data you care about (it is deliberately separate from `DATABASE_URL`, which tests override to in-memory SQLite):

```bash
docker exec neoguard-db-1 psql -U neoguard -d postgres -c "create database neoguard_test"
export TEST_DATABASE_URL=postgresql://neoguard:<password>@127.0.0.1:55432/neoguard_test
```

## What is tested

| Area | Location | Covers |
|---|---|---|
| Ingestion | `tests/unit/test_ingestion.py` | request parameters, retry/backoff, `Retry-After`, bounded retries, 4xx not retried, malformed/truncated responses, write-once raw files, sha256 provenance, snapshot cache |
| Validation | `tests/unit/test_validation.py` | every schema rule (parametrised bad records), reasons recorded, wrong-length rows, duplicates, orphan approaches, PHA-rule audit, CSV round-trip types |
| Features / split | `tests/unit/test_features_preprocessing.py` | feature schema/order, angle encoding, statelessness, chronological split, exclusions, duplicate handling |
| Metrics / artifacts | `tests/unit/test_metrics_artifacts.py` | hand-computed metrics, undefined AUC, thresholds, bootstrap determinism, strict JSON (NaN), immutable versions |
| Leakage | `tests/ml/test_leakage.py` | audit covers every column, target-defining columns never inputs, split disjointness, DB schema parity, **canary** proving H+MOID would make the task trivial |
| Training | `tests/ml/test_training.py` | six artifacts, train-only scaler, validation-only threshold, reproducibility, valid probabilities, metadata completeness, test split untouched |
| Inference / SHAP | `tests/ml/test_predict_explain.py` | output contract, SHAP additivity for all models, train/serve parity, incompatible feature version refused |
| Evaluation | `tests/ml/test_evaluate.py` | test metrics + CIs stored, experiment log idempotent, wrong-dataset refusal |
| Loader | `tests/integration/test_loader.py` | idempotent load, window replacement (no stale rows), unknown objects skipped, registry sync keeps human status |
| API | `tests/integration/test_api.py` | every endpoint (success + failure): pagination, filters, search escaping, sort whitelist, 404/400/422/429/500/503, prediction (default/pinned/promoted model, persistence, out-of-domain input, missing/escaping artifact), analytics (populated and empty), CORS, security headers, health degradation, OpenAPI |
| CLIs | `tests/integration/test_cli.py` | every documented command end to end (mock JPL transport), cache reuse, loud failure when JPL is down |
| PostgreSQL | `tests/integration/test_postgres.py` | Alembic upgrade/downgrade, JSONB types, loader and analytics on real PostgreSQL |

## Synthetic data policy

Tests use generated data only, labelled **`SYNTHETIC / TEST DATA`** (`tests/helpers.py`: designations
`TEST-#####`, `_fixture_notice` in every JSON envelope). It is created in pytest temp directories and
in-memory databases — never under `data/` or `ml/artifacts/`, and never presented as NASA data. The
synthetic "PHA" rule is made up to give models something learnable.

## Verified manually (not automated)

Recorded because automated tests cannot replace them; results in [`HANDOFF.md`](HANDOFF.md):

* **Live JPL ingestion** (real network) — 42,477 SBDB + 30,828 CAD records, 2026-09-21. There are no
  automated network tests, so the live client is exercised only by running `python -m ml.ingestion`.
* **Real-data pipeline, database load (twice, idempotent), API smoke test, prediction with SHAP.**
* **Docker**: image build, `docker compose up` (db → migrate → backend), container health check, non-root user.

## Not yet tested

Frontend and browser E2E (no frontend), load/performance testing, penetration testing,
`pip-audit`, deployment on Render/Vercel.

## Notes

Two third-party deprecation warnings appear in the run (Starlette's `TestClient` about `httpx`, anyio's
`BlockingPortal` alias); they do not affect results.

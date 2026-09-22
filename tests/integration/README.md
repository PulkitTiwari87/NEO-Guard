# Tests — Integration

`test_loader.py` (idempotent load, window replacement, registry sync), `test_api.py` (every endpoint over
in-memory SQLite: success and failure paths, security, CORS, rate limit, OpenAPI), `test_postgres.py`
(Alembic migration and loader on real PostgreSQL; skipped unless `TEST_DATABASE_URL` points to a
**disposable** database — it drops its tables). Data is **SYNTHETIC / TEST DATA**.
Run: `pytest tests/integration`.

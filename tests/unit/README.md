# Tests — Unit

`test_ingestion.py` (client retry/backoff/validation, write-once raw storage), `test_validation.py`
(schema rules, rejection reasons, PHA-rule audit), `test_features_preprocessing.py` (features, chronological
split), `test_metrics_artifacts.py` (hand-computed metrics, strict-JSON artifacts).
All data is **SYNTHETIC / TEST DATA** (`tests/helpers.py`). Run: `pytest tests/unit`.

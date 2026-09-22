# Data Pipeline

> **Status: IMPLEMENTED.** Every command below exists and was run against the real JPL data
> on 2026-09-21. Run them from the repository root after `pip install -r backend/requirements-dev.txt`
> and `pip install -e . --no-deps`.

## Stages

```
JPL SBDB + CAD APIs
      |  python -m ml.ingestion            [ml/ingestion/]
      v
RAW      data/raw/<source>/<YYYY-MM-DD>/<source>_<UTC stamp>.json  (+ .meta.json)   write-once
      |  python -m ml.validation           [ml/validation/]
      v
INTERIM  data/interim/{neo_objects,close_approaches}.csv, rejected_*.jsonl, validation_report.json
      |  python -m ml.preprocessing        [ml/preprocessing/]
      v
PROCESSED data/processed/neo_ml_dataset.csv, split_manifest.json
      |  python -m ml.training             [ml/training/]
      v
ARTIFACTS ml/artifacts/<model>/v<N>/{model.joblib, metadata.json}
      |  python -m ml.evaluation           [ml/evaluation/]   held-out test metrics, curves, docs/EXPERIMENTS.md
      |  python -m ml.explainability       [ml/explainability/]   global SHAP
      v
DATABASE  python -m app.cli load-data      interim -> PostgreSQL (upsert)
          python -m app.cli sync-models    artifacts -> models/experiments tables
```

`make pipeline` runs the `ml` stages in order. Feature engineering has no stage of its own: it is
`ml/features/engineering.py`, used inside the trained pipeline so training and serving are identical.

## Commands and results (real run)

| Command | Result on 2026-09-21 |
|---|---|
| `python -m ml.ingestion` | 42,477 SBDB + 30,828 CAD records fetched (2 requests); `--force` bypasses the 24 h cache |
| `python -m ml.validation` | 42,477 / 30,828 valid, **0 rejected**; PHA-rule audit 42,301/42,351 agree |
| `python -m ml.preprocessing` | 42,351 ML rows (126 without target excluded, 0 duplicate vectors); split 31,545 / 5,790 / 5,016 |
| `python -m ml.training` | 6 models trained in ~11 s |
| `python -m ml.evaluation` | test metrics + 6 entries appended to `docs/EXPERIMENTS.md` |
| `python -m ml.explainability` | `shap_global.json` per model |
| `python -m app.cli load-data` | 42,477 NEOs + 30,828 approaches loaded; 2nd run: 0 inserted / 42,477 updated |

Failures are explicit: ingestion exits non-zero with `INGESTION FAILED: …` when JPL is unavailable
(after bounded retries); later stages exit non-zero when their input is missing.

## Immutability

> **RAW DATA IS NEVER MODIFIED.** Raw files are opened with exclusive-create mode (`"xb"`); a second
> write to the same path raises `FileExistsError`. Interim/processed files are derived and are
> regenerated (overwritten) by re-running their stage. Raw and derived data are git-ignored.

## Provenance

Each raw file has a sidecar `*.meta.json`: source, endpoint, request parameters, retrieval time (UTC),
HTTP status, API version, record count, field list, and `sha256` of the exact response bytes. The
validation report copies these plus reject counts and the dataset version
(`jpl-sbdb-neo-<date>-<sha256[:8]>`). The database `data_sources` table stores the same provenance,
unique per `(source, checksum)`. `split_manifest.json` records the dataset/feature version, the
requested and actual split, exclusion counts, and the leakage checks.

## Idempotency

* Ingestion: identical parameters within 24 h reuse the cached snapshot; otherwise a new raw file.
* `load-data`: NEO objects are upserted on `spkid`; a CAD snapshot **replaces** all approaches in its
  date window (so approaches whose orbit solution changed do not linger as stale duplicates);
  `data_sources` is unique per snapshot checksum. Running it repeatedly never duplicates rows.
* `sync-models`: upserts by `version`; a status set by a human (`set-status`) is preserved.

## Rejected records

`data/interim/rejected_neo_objects.jsonl` / `rejected_close_approaches.jsonl` list every rejected
record with `reasons` and the original source row. Rows with the wrong number of values,
out-of-range values, orbit inconsistencies, duplicates and orphan approaches are rejected — never
silently dropped or truncated. (The real snapshot produced none; the rejection paths are covered by
tests with deliberately bad synthetic rows.)

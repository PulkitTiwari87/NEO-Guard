# Database Schema

> **Status: IMPLEMENTED** (PostgreSQL 16, SQLAlchemy 2.0 ORM in `backend/app/db/models.py`,
> migration `backend/alembic/versions/0001_initial_schema.py`). Verified on PostgreSQL: the schema
> builds from scratch with `alembic upgrade head` (~1 s), `downgrade base` is clean, and the real data
> (42,477 NEOs, 30,828 approaches) loads idempotently. JSON columns are `JSONB` on PostgreSQL
> (plain `JSON` on SQLite, used by the unit tests).

Reproduce: `alembic -c backend/alembic.ini upgrade head` (needs `DATABASE_URL`). Never edit the schema by
hand; change the models and add an Alembic revision.

## Tables

### `neo_objects` — near-Earth asteroids (JPL SBDB)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | BIGINT **PK** (no autoincrement) | no | JPL SPK-ID |
| `designation` | VARCHAR(64) **UNIQUE** | no | primary designation (`pdes`) |
| `full_name` | VARCHAR(128) | no | |
| `name` | VARCHAR(128) | yes | |
| `is_potentially_hazardous` | BOOLEAN | yes | JPL flag; null when MOID is unavailable |
| `absolute_magnitude_h`, `diameter_km`, `albedo` | FLOAT | yes | |
| `eccentricity`, `semi_major_axis_au`, `perihelion_distance_au`, `aphelion_distance_au`, `inclination_deg`, `ascending_node_deg`, `argument_of_perihelion_deg`, `mean_anomaly_deg`, `mean_motion_deg_per_day`, `orbital_period_days`, `epoch_jd`, `rms` | FLOAT | no | orbital elements / fit quality |
| `earth_moid_au` | FLOAT | yes | |
| `condition_code` | VARCHAR(4) | yes | |
| `first_obs_date`, `last_obs_date` | VARCHAR(16) | no | source text (may contain `??`) |
| `first_obs_year`, `n_obs_used` | INTEGER | no | |
| `data_arc_days` | INTEGER | yes | |
| `orbit_class` | VARCHAR(8) | no | |
| `data_source_id` | INTEGER FK → `data_sources.id` | yes | provenance |
| `created_at`, `updated_at` | TIMESTAMPTZ default `now()` | no | `updated_at` refreshed by each upsert |

### `close_approaches` — predicted Earth approaches (JPL CAD)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `neo_id` | BIGINT FK → `neo_objects.id` **ON DELETE CASCADE** | no | |
| `body` | VARCHAR(16) | no | `Earth` |
| `orbit_id` | VARCHAR(16) | yes | |
| `approach_jd` | FLOAT | no | JD, TDB |
| `approach_time_tdb` | TIMESTAMP (naive) | no | **TDB**, not UTC |
| `distance_au`, `distance_min_au`, `distance_max_au` | FLOAT | no | |
| `v_rel_km_s` | FLOAT | no | |
| `v_inf_km_s` | FLOAT | yes | |
| `time_uncertainty` | VARCHAR(16) | yes | JPL text |
| `absolute_magnitude_h` | FLOAT | yes | |
| `data_source_id` | INTEGER FK | yes | |
| `created_at` | TIMESTAMPTZ | no | |

Constraints/indexes: `UNIQUE (neo_id, body, approach_jd)`; index `ix_close_approaches_time
(approach_time_tdb)` for the per-year analytics and the window replacement done on every reload.
Lookups by `neo_id` use the unique constraint's leading column.

### `data_sources` — provenance of each ingested snapshot

`id`, `source_name` (`jpl_sbdb`/`jpl_cad`), `url`, `params` (JSONB), `retrieved_at`, `record_count`,
`rejected_count`, `schema_version` (API version), `dataset_version`, `checksum` (sha256 of the raw response),
`created_at`. **UNIQUE (`source_name`, `checksum`)** → registering the same snapshot twice is a no-op.

### `models` — model registry

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `version` | VARCHAR(64) **UNIQUE** | e.g. `random_forest-v1` |
| `name`, `algorithm` | VARCHAR(64) | |
| `artifact_path` | VARCHAR(256) | relative to `MODEL_DIR`; **never exposed by the API** |
| `dataset_version`, `feature_version` | VARCHAR | |
| `status` | VARCHAR(16) | `experimental` \| `validated` \| `production` \| `deprecated`; set by humans |
| `threshold` | FLOAT | validation-tuned decision threshold |
| `parameters`, `metrics`, `features`, `split` | JSONB | metrics = `{validation, test}` |
| `created_at` | TIMESTAMPTZ | training time |
| `registered_at` | TIMESTAMPTZ | |

### `experiments`

`id`, `experiment_id` **UNIQUE**, `model_version` FK → `models.version`, `dataset_version`,
`config` (JSONB: algorithm, class weighting, parameters, seed, threshold, split, library versions),
`metrics` (JSONB), `created_at`.

### `predictions`

`id`, `neo_id` (BIGINT FK → `neo_objects.id`, ON DELETE CASCADE, **nullable**, indexed), `model_version`
FK → `models.version`, `prediction` (INTEGER 0/1), `probability`, `features` (JSONB), `explanation`
(JSONB, nullable), `created_at`. Rows exist only for predictions that named a known `neo_id`.

## Relationships

```
data_sources 1 --- * neo_objects        data_sources 1 --- * close_approaches
neo_objects  1 --- * close_approaches   neo_objects  1 --- * predictions
models       1 --- * predictions        models       1 --- * experiments
```

## Changes from the planned schema (and why)

| Planned | Implemented | Why |
|---|---|---|
| `neo_objects.id` UUID/SERIAL + `neo_reference_id` | `id` = SPK-ID (BIGINT PK) | JPL's stable natural key; one column, no surrogate |
| `predictions.neo_id` NOT NULL, `prediction` VARCHAR | nullable `neo_id`, `prediction` INTEGER | The API predicts from arbitrary elements; only NEO-linked predictions are stored (bounded table growth) |
| `data_sources`: name, url, retrieved_at, record_count, schema_version, checksum | + `params`, `rejected_count`, `dataset_version`; unique per snapshot | Idempotent registration and full provenance |
| `models`: version, name, parameters, metrics, features, created_at | + `algorithm`, `artifact_path`, `dataset_version`, `feature_version`, `status`, `threshold`, `split` | Registry requirements (versioned, status-managed, never auto-promoted) |
| `close_approaches` "orbiting_body" | `body` | Shorter; the API still exposes `orbiting_body` |

## Load semantics (idempotent)

`python -m app.cli load-data`: NEOs upserted on `id`; each CAD snapshot **replaces** all approaches of
its body/date window (removes stale rows when an orbit solution changes) inside one transaction;
approaches of unknown objects are skipped and counted, never given an invented parent.
`python -m app.cli sync-models` upserts by `version` and keeps a human-set `status`.

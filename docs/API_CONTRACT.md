# API Contract

> **Status: IMPLEMENTED and verified** against real data (2026-09-21). This document describes the
> running backend (`backend/app`). The machine-readable source of truth is the generated OpenAPI
> document at **`/openapi.json`** (also `/docs` Swagger UI and `/redoc`); the two are tested to list
> the same eight paths. Frontend-oriented guidance: [`FRONTEND_CONTRACT.md`](FRONTEND_CONTRACT.md).

Base path: `/api`. All responses are JSON. Times are ISO-8601. Errors: see the end.

## Changes from the foundation contract (and why)

| Area | Foundation contract | Implemented | Why |
|---|---|---|---|
| `GET /health` | `status: "healthy"`, `version`, `timestamp` | `status: "ok" \| "degraded"`, **`database: "ok" \| "unavailable"`**, `version`, `timestamp`; **HTTP 503** when the DB is down | Must report real dependency state so Docker/Render health checks fail when the DB is unreachable |
| NEO `id` | string | **integer** (JPL SPK-ID, e.g. `20099942`) | SPK-ID is the stable natural key; the DB primary key |
| NEO diameter | `estimated_diameter_km_min/max` | **`diameter_km`** (measured, mostly `null`) | JPL SBDB publishes one measured diameter (2.9% of objects), no min/max; deriving a range from H would need an assumed albedo, i.e. an invented value |
| NEO list item | id, name, designation, hazard flag, H, diameter | adds `full_name`, `orbit_class`; `is_potentially_hazardous` may be **`null`** (126 objects lack a MOID) | Real source schema |
| `GET /neos` params | `page, per_page, is_hazardous, search` | adds **`sort`**; `per_page ≤ 100`; `search ≤ 100` chars | Explorer needs sorting; bounds protect the DB |
| Approach fields | `date, relative_velocity_km_s, miss_distance_km, orbiting_body` | same names, plus `miss_distance_au`, `miss_distance_min_au/max_au`, `v_inf_km_s`, `time_uncertainty`, `time_scale` | Source provides uncertainty bounds; `date` is **TDB**, not UTC |
| `POST /predict` request | `{"features": {}}` (TBD) | `features` = 7 orbital elements; optional **`model_version`**, **`neo_id`**; query `explain` | Feature set now fixed by the trained models |
| `POST /predict` response | `prediction: string` | **`prediction: 0 \| 1`**, `label`, `probability`, `threshold`, `model_version`, **`model_status`**, structured `explanation`, `disclaimer` | Integer class + explicit status/threshold so clients cannot mistake an experimental model for a validated one |
| Models | `version, name, created_at, metrics` | adds `algorithm, status, dataset_version, feature_version`; detail adds `threshold, features, input_features, parameters, split` | Registry fields required by the scientific-integrity rules |
| Analytics | `total_neos, hazardous_count, non_hazardous_count, total_approaches, summary` | adds `unknown_hazard_count`, `orbit_class_counts`, `approaches_by_year`; `summary` populated | Real, computable aggregates only |

## `GET /api/health`

`200` (or `503` when the database is unreachable):
```json
{ "status": "ok", "database": "ok", "version": "0.1.0", "timestamp": "2026-09-21T13:30:54.793406Z" }
```
`503` body: `{"status": "degraded", "database": "unavailable", ...}`.

## `GET /api/neos`

| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int ≥ 1 | 1 | |
| `per_page` | int 1–100 | 20 | |
| `is_hazardous` | bool | – | Filter on JPL's PHA flag (objects with unknown flag match neither value) |
| `search` | string ≤ 100 | – | Case-insensitive substring of designation, full name or name; `%`/`_` are literal |
| `sort` | string | `id` | One of `id, designation, name, absolute_magnitude_h, diameter_km, semi_major_axis_au, eccentricity, inclination_deg, earth_moid_au, first_obs_year`; prefix `-` for descending. Nulls last. |

`200`:
```json
{
  "items": [{
    "id": 20003122, "name": "Florence", "designation": "3122",
    "full_name": "3122 Florence (1981 ET3)", "is_potentially_hazardous": true,
    "absolute_magnitude_h": 14.08, "diameter_km": 4.9, "orbit_class": "AMO"
  }],
  "total": 2549, "page": 1, "per_page": 2
}
```
`400` unknown sort field · `422` invalid parameter. A page past the end returns `items: []` with the true `total`.

## `GET /api/neos/{id}`

`id` = SPK-ID (integer ≥ 1). `200`: all list-item fields plus `albedo`, `orbital_data` and
`close_approaches` (time-ordered, same shape as below):
```json
{
  "id": 20099942, "name": "Apophis", "designation": "99942", "full_name": "99942 Apophis (2004 MN4)",
  "is_potentially_hazardous": true, "absolute_magnitude_h": 19.09, "diameter_km": 0.34,
  "orbit_class": "ATE", "albedo": 0.35,
  "orbital_data": {
    "eccentricity": 0.1911492279663492, "semi_major_axis_au": 0.9223592206975018,
    "perihelion_distance_au": 0.7460509677535309, "aphelion_distance_au": 1.098667473641473,
    "inclination_deg": 3.340996879880978, "ascending_node_deg": 203.8936514240762,
    "argument_of_perihelion_deg": 126.6795706895841, "mean_anomaly_deg": 175.3304026592739,
    "mean_motion_deg_per_day": 1.112638115271892, "orbital_period_days": 323.5553366891694,
    "earth_moid_au": 0.000107917, "epoch_jd": 2461200.5, "condition_code": "0",
    "first_obs_date": "2004-03-15", "last_obs_date": "2022-04-09", "n_obs_used": 7370,
    "data_arc_days": 6599, "rms": 0.25657
  },
  "close_approaches": [ "…same objects as in /approaches below…" ]
}
```
(Real response for Apophis from the 2026-09-21 snapshot.) `404 {"detail": "NEO not found"}`, `422` for a non-integer id.

## `GET /api/neos/{id}/approaches`

Predicted Earth close approaches (≤ 0.05 au, 2000–2100) of that object, oldest first.
```json
{
  "neo_id": 20099942,
  "approaches": [
    {
      "date": "2029-04-13T21:46:00", "time_scale": "TDB", "orbiting_body": "Earth",
      "miss_distance_au": 0.0002540909104192, "miss_distance_km": 38011.45916293676,
      "miss_distance_min_au": 0.0002540689999763, "miss_distance_max_au": 0.0002541128210176,
      "relative_velocity_km_s": 7.42253895678452, "v_inf_km_s": 5.84135589753103,
      "time_uncertainty": "< 00:01"
    },
    {
      "date": "2051-04-20T02:05:00", "time_scale": "TDB", "orbiting_body": "Earth",
      "miss_distance_au": 0.0414902230254537, "miss_distance_km": 6206849.019475985,
      "miss_distance_min_au": 0.0399038645943395, "miss_distance_max_au": 0.0430769570279036,
      "relative_velocity_km_s": 4.69385481977169, "v_inf_km_s": 4.68015322050512,
      "time_uncertainty": "08:07"
    }
  ]
}
```
(Real response for Apophis, 2026-09-21 snapshot.) An object with no stored approach returns
`approaches: []` (200). `404` for an unknown NEO.

## `POST /api/predict`

Query: `explain` (bool, default `true`). Body:
```json
{
  "features": {
    "semi_major_axis_au": 0.9223592206975018, "eccentricity": 0.1911492279663492,
    "inclination_deg": 3.340996879880978, "perihelion_distance_au": 0.7460509677535309,
    "aphelion_distance_au": 1.098667473641473, "ascending_node_deg": 203.8936514240762,
    "argument_of_perihelion_deg": 126.6795706895841
  },
  "model_version": "random_forest-v1",
  "neo_id": 20099942
}
```
`model_version` (optional) defaults to the best available model (status first — `production` >
`validated` > `experimental`, never `deprecated` — then validation PR-AUC; or the version pinned by
`ACTIVE_MODEL_VERSION`). `neo_id` (optional) stores the prediction in the `predictions` table for that NEO;
anonymous predictions are **not** stored.

Validation (`422`): unknown extra fields are rejected (notably `absolute_magnitude_h`, which is not a
model input); `0 ≤ e < 1`; `0 ≤ i ≤ 180`; angles `0–360`; `0 < q ≤ 1.3`; `q ≈ a(1−e)` and `Q ≈ a(1+e)` (1e-4 relative).

`200` (the real response for the request above; `contributions` truncated to the first three of nine —
all nine features are always returned):
```json
{
  "prediction": 0, "label": "not_potentially_hazardous",
  "probability": 0.17632985069053195, "threshold": 0.2702955552073201,
  "model_version": "random_forest-v1", "model_status": "experimental",
  "explanation": {
    "method": "SHAP", "output_space": "probability", "base_value": 0.07520515665451472,
    "contributions": [
      {"feature": "perihelion_distance_au", "value": 0.7460509677535309, "shap_value": 0.05205195814964512},
      {"feature": "argument_of_perihelion_sin", "value": 0.8019886817365375, "shap_value": 0.01965678030394149},
      {"feature": "eccentricity", "value": 0.1911492279663492, "shap_value": -0.01950968193139638}
    ]
  },
  "disclaimer": "Statistical estimate from seven orbital elements only. It is not JPL's PHA designation (which also requires absolute magnitude H) and not an impact-risk assessment."
}
```
* `prediction = 1` iff `probability ≥ threshold` (threshold tuned on validation, differs per model).
* `probability` is `predict_proba` of the positive class; for `*_balanced` models it is **not** a calibrated probability.
* `explanation` contributions sum with `base_value` to the model output; `output_space` is `log_odds`
  (logistic regression, XGBoost) or `probability` (random forest). `null` when `explain=false` or the
  model has no explainability artifacts. SHAP describes the model, not causes.
* `404` unknown `model_version` or `neo_id` · `503 {"detail": "No trained model is available"}` or
  `{"detail": "Model artifact unavailable"}`.

## `GET /api/models` and `GET /api/models/{version}`

List: `{"models": [{version, name, algorithm, status, created_at, dataset_version, feature_version, metrics}]}`,
newest first. `metrics` = `{"validation": {...}, "test": {...}}` with `accuracy, precision, recall, f1,
roc_auc, pr_auc, threshold, n, n_positive, prevalence, confusion_matrix{tn,fp,fn,tp}`; `test` also has
`bootstrap_ci{roc_auc[2], pr_auc[2], n_resamples}`. Detail adds `threshold`, `features` (engineered inputs),
`input_features` (raw fields for `/predict`), `parameters`, `split`. Artifact paths are never exposed.
`status ∈ experimental | validated | production | deprecated`. `404 {"detail": "Model not found"}`.

## `GET /api/analytics`

Computed from stored data on every call (a fresh database returns zeros and nulls):
```json
{
  "total_neos": 42477, "hazardous_count": 2549, "non_hazardous_count": 39802, "unknown_hazard_count": 126,
  "total_approaches": 30828,
  "orbit_class_counts": {"APO": 24157, "AMO": 14823, "ATE": 3459, "IEO": 38},
  "approaches_by_year": [{"year": 2000, "count": 155}, "..."],
  "summary": {
    "diameter_km": {"count": 1245, "min": 0.0025, "max": 37.675, "mean": 1.0341, "median": 0.629},
    "absolute_magnitude_h": {"...": "..."}, "relative_velocity_km_s": {"...": "..."}, "miss_distance_au": {"...": "..."}
  },
  "upcoming_close_approaches": [
    {"neo": {"id": 20099942, "name": "Apophis", "designation": "99942", "...": "NeoSummary fields"},
     "approach": {"date": "2029-04-13T21:46:00", "...": "same Approach shape as /neos/{id}/approaches"}}
  ]
}
```
Each summary is `null` when there is no data. (Counts above are the real values for dataset `jpl-sbdb-neo-20260921-c34b5103`.)

`upcoming_close_approaches` (added Phase 3.5, additive): the soonest ≤8 stored close approaches with
`approach.date >= now` (TDB treated as UTC; offset is under two minutes and immaterial here), sorted
ascending, each item nesting the real `NeoSummary` and `Approach` shapes documented above. Empty list
when nothing in the database is upcoming. Powers the command-dashboard's close-approach panel with
real data instead of a fabricated feed.

## Errors

Always `{"detail": ...}`; no stack traces, credentials or filesystem paths.

| Status | Body `detail` | When |
|---|---|---|
| 400 | string | Unsupported `sort` field |
| 404 | `"NEO not found"`, `"Model not found"`, `"Model version '…' not found"` | Unknown resource |
| 422 | list of `{loc, msg, type}` (submitted values are not echoed) | Invalid path/query/body |
| 429 | `"Rate limit exceeded"` (+ `Retry-After` header) | Per-client limit (default 120/min; `/api/health` exempt) |
| 500 | `"Internal server error"` | Unexpected error (details only in server logs) |
| 503 | `"Database unavailable"`, `"No trained model is available"`, `"Model artifact unavailable"`, `"Prediction failed"` | Dependency problem |

Every response carries `X-Request-ID`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer`, `Cache-Control: no-store`. CORS allows only origins in `CORS_ORIGINS`
(GET, POST; no credentials).

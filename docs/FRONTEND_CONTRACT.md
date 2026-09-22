# Frontend Contract

> **Status: BACKEND SIDE IMPLEMENTED — frontend NOT implemented.** This is the contract for the
> Phase-3 frontend (Antigravity + Stitch, Apple-inspired design). The backend below is running and
> verified; the frontend must consume it and must not access the database. Field-level truth:
> [`API_CONTRACT.md`](API_CONTRACT.md) and the live **`/openapi.json`** (generate TypeScript types from it).

Backend base URL is configuration on the frontend side (local dev: `http://localhost:8000`).
The backend allows CORS from `CORS_ORIGINS` (default `http://localhost:5173`, the Vite dev server) for GET/POST.

## Pages and the endpoints they use

| Route | Page | Endpoints |
|-------|------|-----------|
| `/` | Dashboard (key metrics, recent data) | `GET /api/analytics`, `GET /api/health` |
| `/neos` | NEO Explorer (search, filter, sort, paginate) | `GET /api/neos` |
| `/neos/:id` | NEO Detail (orbit, approaches, "Predict for this object") | `GET /api/neos/{id}`, `GET /api/neos/{id}/approaches`, `POST /api/predict` |
| `/analytics` | Analytics (distributions, approaches per year) | `GET /api/analytics` |
| `/models` | Model performance (metrics, versions, status) | `GET /api/models`, `GET /api/models/{version}` |
| `/predict` | Prediction + explanation | `POST /api/predict`, `GET /api/models` |
| `/about` | Methodology and limitations | none (content from `docs/`) |

## Response shapes (TypeScript)

```ts
type Health = { status: "ok" | "degraded"; database: "ok" | "unavailable"; version: string; timestamp: string };

type NeoSummary = {
  id: number;                       // JPL SPK-ID — stable key, use in routes
  name: string | null;              // only ~0.4% of objects have a name
  designation: string; full_name: string;
  is_potentially_hazardous: boolean | null;   // null = flag unavailable (no MOID)
  absolute_magnitude_h: number | null;
  diameter_km: number | null;       // measured; null for ~97% of objects
  orbit_class: string;              // APO | AMO | ATE | IEO
};
type NeoList = { items: NeoSummary[]; total: number; page: number; per_page: number };

type OrbitalData = {
  eccentricity: number; semi_major_axis_au: number; perihelion_distance_au: number; aphelion_distance_au: number;
  inclination_deg: number; ascending_node_deg: number; argument_of_perihelion_deg: number;
  mean_anomaly_deg: number; mean_motion_deg_per_day: number; orbital_period_days: number;
  earth_moid_au: number | null; epoch_jd: number; condition_code: string | null;
  first_obs_date: string; last_obs_date: string; n_obs_used: number; data_arc_days: number | null; rms: number;
};
type Approach = {
  date: string;                     // ISO-8601, TDB, NO timezone suffix
  time_scale: "TDB"; orbiting_body: string;
  miss_distance_au: number; miss_distance_km: number; miss_distance_min_au: number; miss_distance_max_au: number;
  relative_velocity_km_s: number; v_inf_km_s: number | null; time_uncertainty: string | null;
};
type NeoDetail = NeoSummary & { albedo: number | null; orbital_data: OrbitalData; close_approaches: Approach[] };
type ApproachList = { neo_id: number; approaches: Approach[] };

type PredictFeatures = {
  semi_major_axis_au: number; eccentricity: number; inclination_deg: number;
  perihelion_distance_au: number; aphelion_distance_au: number;
  ascending_node_deg: number; argument_of_perihelion_deg: number;
};
type PredictRequest = { features: PredictFeatures; model_version?: string; neo_id?: number };
type Contribution = { feature: string; value: number; shap_value: number };
type PredictResponse = {
  prediction: 0 | 1; label: "potentially_hazardous" | "not_potentially_hazardous";
  probability: number; threshold: number; model_version: string; model_status: string;
  explanation: null | { method: "SHAP"; output_space: "log_odds" | "probability"; base_value: number; contributions: Contribution[] };
  disclaimer: string;
};

type Metrics = {                     // per split; test also has bootstrap_ci
  n: number; n_positive: number; prevalence: number; threshold: number;
  accuracy: number; precision: number; recall: number; f1: number;
  roc_auc: number | null; pr_auc: number | null;
  confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
  bootstrap_ci?: { roc_auc: [number, number]; pr_auc: [number, number]; n_resamples: number };
};
type ModelSummary = {
  version: string; name: string; algorithm: string;
  status: "experimental" | "validated" | "production" | "deprecated";
  created_at: string; dataset_version: string; feature_version: string;
  metrics: { validation?: Metrics; test?: Metrics };
};
type ModelDetail = ModelSummary & { threshold: number; features: string[]; input_features: string[] | null; parameters: object; split: object };

type NumericSummary = { count: number; min: number; max: number; mean: number; median: number };
type UpcomingApproach = { neo: NeoSummary; approach: Approach };
type Analytics = {
  total_neos: number; hazardous_count: number; non_hazardous_count: number; unknown_hazard_count: number;
  total_approaches: number; orbit_class_counts: Record<string, number>;
  approaches_by_year: { year: number; count: number }[];
  summary: { diameter_km: NumericSummary | null; absolute_magnitude_h: NumericSummary | null;
             relative_velocity_km_s: NumericSummary | null; miss_distance_au: NumericSummary | null };
  /** Soonest ≤8 stored close approaches at/after now, sorted ascending. Added Phase 3.5. */
  upcoming_close_approaches: UpcomingApproach[];
};
```

## Behaviour the UI must handle

* **Pagination:** `page` (≥ 1), `per_page` (1–100, default 20); `total` is the full filtered count.
  A page beyond the end returns `items: []`.
* **Filtering / search / sorting:** `is_hazardous=true|false` (objects with an unknown flag match neither);
  `search` (≤ 100 chars, substring of designation/full name/name, case-insensitive); `sort=<field>` or
  `sort=-<field>` from `id, designation, name, absolute_magnitude_h, diameter_km, semi_major_axis_au,
  eccentricity, inclination_deg, earth_moid_au, first_obs_year` (nulls last).
* **Errors** are `{"detail": string}` except `422`, where `detail` is `{loc, msg, type}[]` (map `loc`
  to form fields). Codes: 400 bad sort, 404 unknown NEO/model, 422 invalid input, 429 rate limited
  (honour `Retry-After`), 500 generic, 503 dependency down / no model. Show friendly messages;
  never show raw `detail` for 5xx.
* **Health:** `503` with `status: "degraded"` means the database is down; show a status banner.
* **Empty states are real:** a database without data returns zeros/`null` and `items: []`, and
  `/api/models` returns `{"models": []}`; render "no data yet", never placeholder numbers.
* **Nulls are normal:** `diameter_km`, `albedo`, `name`, `is_potentially_hazardous`, `earth_moid_au`,
  `v_inf_km_s` can be `null`. Do not coerce to 0.
* **Dates:** approach `date` is **TDB**, not UTC; label it (`time_scale`). Show `time_uncertainty` and the
  `min/max` distance bounds — future approaches are predictions.
* **Units:** au and km/s as given; `miss_distance_km` is provided (au × 149,597,870.7).

## Prediction UX requirements (scientific integrity)

1. Always show **`model_version`** and **`model_status`** (all current models are `experimental`)
   and the **`disclaimer`** text next to any prediction.
2. Present `probability` and the `label` together with the `threshold`; do not call it a "hazard
   probability" or a risk. Models named `*_balanced` output probabilities that are not calibrated.
3. Show JPL's own `is_potentially_hazardous` beside the model result for stored objects; the model is
   frequently wrong (validation/test recall ≈ 0.4) — the UI must not imply otherwise.
4. SHAP explanation: bar chart of `contributions` (already sorted by |impact|); label the unit from
   `output_space` (`log_odds` or `probability`); wording must say "influence on the model's output",
   **not** "cause".
5. `422` on prediction inputs means physically inconsistent or out-of-domain elements (e.g. q > 1.3 au):
   surface the message; the model only covers near-Earth asteroids.
6. `POST /api/predict` accepts only the seven fields above — **not** `absolute_magnitude_h` or MOID.

## Models page

Show each version's `status`, dataset/feature versions, validation **and** test metrics with the
bootstrap intervals (test set has only 64 positives), and the confusion matrices. Compare PR-AUC to
the no-skill level (`prevalence`). Curves (ROC/PR points) are in `ml/artifacts/<name>/v1/evaluation.json`
and are **not** exposed by the API yet (candidate follow-up if the UI needs charts).

## Planned UI components

Dashboard metric cards; explorer with search/filter/pagination; object detail with orbital data and
approach timeline; analytics charts (per-year counts, distributions); model dashboard (metrics,
confusion matrix); prediction form with SHAP visualisation; methodology/limitations page.

## Technology stack

React, Vite, Tailwind CSS, Stitch (design system), charting library (TBD). Design direction:
[`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md). The frontend consumes only the API above.

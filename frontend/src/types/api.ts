/**
 * TypeScript types matching backend Pydantic schemas exactly.
 * Source of truth: /openapi.json and docs/API_CONTRACT.md
 * Do not add fields that the backend does not provide.
 */

// ─── Health ──────────────────────────────────────────────────────────────────

export interface Health {
  status: 'ok' | 'degraded';
  database: 'ok' | 'unavailable';
  version: string;
  timestamp: string;
}

// ─── NEO ─────────────────────────────────────────────────────────────────────

export interface NeoSummary {
  /** JPL SPK-ID — stable natural key */
  id: number;
  /** Only ~0.4% of objects have a name */
  name: string | null;
  designation: string;
  full_name: string;
  /** null when Earth MOID is unavailable (126 objects) */
  is_potentially_hazardous: boolean | null;
  absolute_magnitude_h: number | null;
  /** Measured diameter; null for ~97% of objects */
  diameter_km: number | null;
  /** APO | AMO | ATE | IEO */
  orbit_class: string;
}

export interface NeoList {
  items: NeoSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface OrbitalData {
  eccentricity: number;
  semi_major_axis_au: number;
  perihelion_distance_au: number;
  aphelion_distance_au: number;
  inclination_deg: number;
  ascending_node_deg: number;
  argument_of_perihelion_deg: number;
  mean_anomaly_deg: number;
  mean_motion_deg_per_day: number;
  orbital_period_days: number;
  earth_moid_au: number | null;
  epoch_jd: number;
  condition_code: string | null;
  first_obs_date: string;
  last_obs_date: string;
  n_obs_used: number;
  data_arc_days: number | null;
  rms: number;
}

export interface Approach {
  /** ISO-8601 datetime in TDB (not UTC) — no timezone suffix */
  date: string;
  /** Always "TDB" */
  time_scale: 'TDB';
  orbiting_body: string;
  miss_distance_au: number;
  miss_distance_km: number;
  miss_distance_min_au: number;
  miss_distance_max_au: number;
  relative_velocity_km_s: number;
  v_inf_km_s: number | null;
  time_uncertainty: string | null;
}

export interface NeoDetail extends NeoSummary {
  albedo: number | null;
  orbital_data: OrbitalData;
  close_approaches: Approach[];
}

export interface ApproachList {
  neo_id: number;
  approaches: Approach[];
}

// ─── Prediction ──────────────────────────────────────────────────────────────

export interface PredictFeatures {
  semi_major_axis_au: number;
  eccentricity: number;
  inclination_deg: number;
  perihelion_distance_au: number;
  aphelion_distance_au: number;
  ascending_node_deg: number;
  argument_of_perihelion_deg: number;
}

export interface PredictRequest {
  features: PredictFeatures;
  model_version?: string;
  neo_id?: number;
}

export interface Contribution {
  feature: string;
  value: number;
  shap_value: number;
}

export interface Explanation {
  method: 'SHAP';
  output_space: 'log_odds' | 'probability';
  base_value: number;
  /** Sorted by |shap_value| descending */
  contributions: Contribution[];
}

export interface PredictResponse {
  prediction: 0 | 1;
  label: 'potentially_hazardous' | 'not_potentially_hazardous';
  /** Uncalibrated model score (predict_proba of the positive class). Field name kept for API
   * compatibility; not demonstrated to be a calibrated probability (docs/EXPERIMENTS.md). */
  probability: number;
  threshold: number;
  model_version: string;
  /** all current models are "experimental" */
  model_status: string;
  explanation: Explanation | null;
  disclaimer: string;
}

// ─── Models ──────────────────────────────────────────────────────────────────

export interface ConfusionMatrix {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
}

export interface BootstrapCI {
  roc_auc: [number, number];
  pr_auc: [number, number];
  n_resamples: number;
}

export interface Metrics {
  n: number;
  n_positive: number;
  prevalence: number;
  threshold: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number | null;
  pr_auc: number | null;
  confusion_matrix: ConfusionMatrix;
  bootstrap_ci?: BootstrapCI;
}

export interface ModelSummary {
  version: string;
  name: string;
  algorithm: string;
  status: 'experimental' | 'validated' | 'production' | 'deprecated';
  created_at: string;
  dataset_version: string;
  feature_version: string;
  metrics: {
    validation?: Metrics;
    test?: Metrics;
  };
}

export interface ModelList {
  models: ModelSummary[];
}

export interface ModelDetail extends ModelSummary {
  threshold: number;
  features: string[];
  input_features: string[] | null;
  parameters: Record<string, unknown>;
  split: Record<string, unknown>;
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export interface NumericSummary {
  count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
}

export interface YearCount {
  year: number;
  count: number;
}

export interface UpcomingApproach {
  neo: NeoSummary;
  approach: Approach;
}

export interface Analytics {
  total_neos: number;
  hazardous_count: number;
  non_hazardous_count: number;
  unknown_hazard_count: number;
  total_approaches: number;
  orbit_class_counts: Record<string, number>;
  approaches_by_year: YearCount[];
  summary: {
    diameter_km: NumericSummary | null;
    absolute_magnitude_h: NumericSummary | null;
    relative_velocity_km_s: NumericSummary | null;
    miss_distance_au: NumericSummary | null;
  };
  /** Soonest ≤8 stored close approaches at/after now, sorted ascending. Empty if none. */
  upcoming_close_approaches: UpcomingApproach[];
}

// ─── API Error ───────────────────────────────────────────────────────────────

export interface ApiError {
  status: number;
  message: string;
  detail?: string | Array<{ loc: string[]; msg: string; type: string }>;
}

// ─── Query params ────────────────────────────────────────────────────────────

export type NeoSortField =
  | 'id' | '-id'
  | 'designation' | '-designation'
  | 'name' | '-name'
  | 'absolute_magnitude_h' | '-absolute_magnitude_h'
  | 'diameter_km' | '-diameter_km'
  | 'semi_major_axis_au' | '-semi_major_axis_au'
  | 'eccentricity' | '-eccentricity'
  | 'inclination_deg' | '-inclination_deg'
  | 'earth_moid_au' | '-earth_moid_au'
  | 'first_obs_year' | '-first_obs_year';

export interface NeoListParams {
  page?: number;
  per_page?: number;
  is_hazardous?: boolean;
  search?: string;
  sort?: NeoSortField;
}

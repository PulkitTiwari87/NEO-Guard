# Data Leakage Prevention Policy

> **Status: IMPLEMENTED and TESTED.** The audit below is the source of truth for the model inputs;
> it is encoded in `ml/features/audit.py` and enforced by `tests/ml/test_leakage.py`.

## Purpose

Prevent any form of data leakage that would produce inflated or unreliable evaluation metrics.

## ⚠️ Scientific ambiguity flagged for human review

The target is JPL's PHA flag, which **is a deterministic rule** (Earth MOID ≤ 0.05 au **and** H ≤ 22.0,
CNEOS). Verified on the real data: the flag matches that rule for 42,301 of 42,351 objects.
Consequences, and the choice made (per `CLAUDE.md`: *document, don't silently assume*):

* `moid` and `H` **define** the label. A model given them re-derives it (the canary test
  `test_canary_target_defining_features_would_make_the_task_trivial` shows near-perfect scores on
  synthetic data). They are **excluded**, as are size proxies (`diameter`, `albedo`).
* What is left — orbital elements — determines the MOID half of the rule (Earth's orbit is fixed) but
  says nothing about H. The models therefore learn **"which orbits can approach Earth closely"**, a
  legitimate but *weaker* task than reproducing JPL's flag. Reported metrics measure exactly that.
* **Decision needed from the human reviewer:** confirm this framing is the intended scientific goal
  (versus, e.g., classifying by MOID alone, or treating H as a legitimate input). No alternative was
  silently adopted.

## Leakage types and how each is handled

| Type | Handling in this project |
|------|--------------------------|
| Target leakage / derived-target | `moid`, `H` excluded; canary test; `test_target_definition_and_size_proxies_are_never_inputs` |
| Train/test contamination | Chronological split (below); no spkid overlap (0); tests assert disjointness |
| Temporal leakage | Split by year of first observation; train < validation < test; `first_obs_*` used for splitting only |
| Duplicate leakage | Exact duplicate feature vectors removed **before** splitting (0 found); `spkid`/`designation` unique (0 duplicates); 0 feature vectors span two splits |
| Preprocessing leakage | Scaler/model live in one sklearn `Pipeline` fitted on `train` only; test asserts `scaler.mean_` equals the train mean and differs from the all-data mean |
| Post-outcome information | Observation-effort metadata (`n_obs_used`, `data_arc_days`, `condition_code`, `rms`, `last_obs_date`) excluded: PHAs receive extra follow-up, so these grow *after* the label is known |
| Evaluation leakage | Threshold tuned on **validation**; test evaluated afterwards, once per candidate; no selection on test |

## Split

Chronological by `first_obs_year` (whole years per split, ≈70/15/15), dataset `jpl-sbdb-neo-20260921-c34b5103`:

| Split | Years | Rows | PHA | PHA rate |
|-------|-------|------|-----|----------|
| train | 1893–2022 | 31,545 | 2,372 | 7.52% |
| validation | 2023–2024 | 5,790 | 113 | 1.95% |
| test | 2025–2026 | 5,016 | 64 | 1.28% |

Why not a random split: the intended use is classifying *newly discovered* objects, and discovery
surveys change what is found (small, faint objects dominate recent years). A random split would let
the model see the same discovery era it is tested on and overstate performance. The price is a
strong distribution shift and a test set with only **64 positives** (wide confidence intervals).
A random-split comparison was **not** run.

## Feature audit (every column of the internal schema)

| Feature | Source | Available at prediction time? | Contains target info? | Temporal risk | Derived from target? | Allowed | Reason |
|---|---|---|---|---|---|---|---|
| `spkid`, `designation`, `full_name`, `name` | SBDB | yes | no | none | no | identifier only | Keys/labels, never inputs |
| `is_potentially_hazardous` | SBDB `pha` | – | **is the target** | – | – | target | |
| `absolute_magnitude_h` | SBDB `H` | yes | **yes** (H ≤ 22 half of the rule) | none | yes | **no** | Re-derives the label |
| `earth_moid_au` | SBDB `moid` | yes | **yes** (MOID ≤ 0.05 half) | none | yes | **no** | Re-derives the label |
| `diameter_km` | SBDB | only for 2.9% | proxy for H | none | proxy | **no** | Size proxy; missingness encodes brightness |
| `albedo` | SBDB | only for 2.8% | proxy | none | proxy | **no** | Comes with measured diameter |
| `eccentricity`, `semi_major_axis_au`, `inclination_deg` | SBDB | yes (any orbit solution) | no (orbit determines MOID, not H) | none | no | **yes** | Keplerian elements |
| `perihelion_distance_au`, `aphelion_distance_au` | SBDB `q`, `ad` | yes | no | none | functions of a, e (not of the target) | **yes** | Published elements; redundant but harmless |
| `ascending_node_deg`, `argument_of_perihelion_deg` | SBDB | yes | no | none | no | **yes** (as sin/cos) | Orientation relative to Earth's orbit affects MOID |
| `mean_anomaly_deg`, `epoch_jd` | SBDB | yes | no | epoch-dependent | no | no | Position along orbit; irrelevant to MOID; noise |
| `mean_motion_deg_per_day`, `orbital_period_days`, `orbit_class` | SBDB | yes | no | none | functions of other inputs | no | Redundant |
| `condition_code`, `n_obs_used`, `data_arc_days`, `rms`, `last_obs_date` | SBDB | only after follow-up | indirectly | **yes** — grows after PHA status is known | no | **no** | Post-outcome / selection effect |
| `first_obs_date`, `first_obs_year` | SBDB | – | no | – | no | split only | Defines the chronological split |

## Residual risks (not eliminated)

* **Discovery bias / distribution shift.** PHA rate falls from 7.5% (train) to 1.3% (test). The
  model cannot see H, so it cannot adjust. `docs/EXPERIMENTS.md` "Distribution shift
  investigation" quantifies this further (orbit-class composition, per-feature KS tests,
  prevalence by discovery year) — the *cause* of the shift remains INCONCLUSIVE from this dataset
  alone; we do not assert why recent discoveries skew smaller.
* **Small test set.** 64 positives; bootstrap intervals are reported and are wide.
* **Test reuse.** All six candidates were evaluated on the same test set (selection was made on
  validation before looking at test). Any further tuning against test invalidates it.
* **Snapshot dependence.** The PHA flag itself can change with new observations.

## Prevention rules (unchanged policy)

1. Split before fitting anything. 2. Chronological splits when data has a time dimension.
3. Deduplicate before splitting. 4. Audit every feature (`ml/features/audit.py`).
5. Fit preprocessing inside the training pipeline only.

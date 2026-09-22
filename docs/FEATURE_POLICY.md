# Feature Policy

## Admission criteria (unchanged)

A feature can be used in the ML pipeline only if **all** hold:

1. It exists in the authoritative dataset (or is a documented derivation of fields that exist).
2. Its meaning is documented in [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).
3. It is available at prediction time (not post-outcome).
4. It does not directly encode the target variable.
5. Its preprocessing is reproducible and documented.

**No invented scientific features.** Every feature traces back to a real SBDB field.
Enforced in code: `ml/features/audit.py` + `tests/ml/test_leakage.py`.

## Feature registry — `features-v1`

Model inputs are the 7 SBDB orbital elements below; `ml.features.engineering.build_features` turns
them into the 9 engineered columns actually seen by the models (`config.FEATURE_COLUMNS`).

| Feature (raw input) | Source | Type | Leakage audit | Allowed |
|---|---|---|---|---|
| `semi_major_axis_au` | SBDB `a` | float, au | pass | yes |
| `eccentricity` | SBDB `e` | float | pass | yes |
| `inclination_deg` | SBDB `i` | float, deg | pass | yes |
| `perihelion_distance_au` | SBDB `q` | float, au | pass | yes |
| `aphelion_distance_au` | SBDB `ad` | float, au | pass | yes |
| `ascending_node_deg` | SBDB `om` | float, deg | pass | yes → sin/cos |
| `argument_of_perihelion_deg` | SBDB `w` | float, deg | pass | yes → sin/cos |

Full per-column audit (including everything excluded and why): [`DATA_LEAKAGE.md`](DATA_LEAKAGE.md).

## Derived features

```
Name:               ascending_node_sin, ascending_node_cos
Source features:    ascending_node_deg (SBDB om)
Formula:            sin(radians(om)), cos(radians(om))
Units:              dimensionless, in [-1, 1]
Transformation:     none beyond the formula; stateless (nothing fitted)
Scientific rationale: om is an angle on a circle (0° = 360°); raw degrees would place 359° and 1° far apart.
Leakage assessment: none — a deterministic function of an audited input available at prediction time.
```

```
Name:               argument_of_perihelion_sin, argument_of_perihelion_cos
Source features:    argument_of_perihelion_deg (SBDB w)
Formula:            sin(radians(w)), cos(radians(w))
Units:              dimensionless, in [-1, 1]
Transformation:     stateless
Scientific rationale: same as above (circular variable).
Leakage assessment: none.
```

`perihelion_distance_au` and `aphelion_distance_au` are **not** derived by us: SBDB publishes them
(`q`, `ad`) and validation verifies `q ≈ a(1−e)`, `Q ≈ a(1+e)`. They are redundant with `a` and `e`
but give the linear model and shallow trees direct access to the quantity that matters physically
(an orbit must reach near 1 au to approach Earth).

## Not features (explicitly)

`absolute_magnitude_h`, `earth_moid_au` (define the target), `diameter_km`, `albedo` (size proxies),
`condition_code`, `n_obs_used`, `data_arc_days`, `rms`, `last_obs_date` (post-outcome observation
effort), `mean_anomaly_deg`, `epoch_jd`, `mean_motion`, `orbital_period`, `orbit_class` (irrelevant or
redundant). `first_obs_year` is used only to build the chronological split.

## Versioning

`FEATURE_VERSION = "features-v1"` is stored in every model's metadata and in the database. Loading
an artifact whose feature version differs from the code is refused
(`ml.inference.predict.IncompatibleArtifact`). Changing the feature set means a new version, new
training, and a new audit entry.

# Data Dictionary

> **Status: FINAL for dataset `jpl-sbdb-neo-20260921-c34b5103`.** Field meanings are taken from the
> official JPL documentation (SBDB Query API 1.0, CAD API 1.5); null counts are measured on the real
> snapshot (42,477 NEOs, 30,828 close approaches). Internal names are defined in
> `ml/validation/schema.py`; the database uses the same names (`neo_objects.id` = `spkid`).

## NEO objects (`neo_objects`, source: SBDB Query API)

| Field (internal) | Source field | Meaning | Type | Unit | Nullable | Transformation | ML input? | API? |
|---|---|---|---|---|---|---|---|---|
| `spkid` (`id`) | `spkid` | JPL SPK-ID, the object's unique numeric key | int | – | no | none | no (identifier) | yes (`id`) |
| `designation` | `pdes` | Primary designation (e.g. `433`, `2011 AG5`) | str | – | no | none | no | yes |
| `full_name` | `full_name` | Full name with provisional designation | str | – | no | whitespace stripped | no | yes |
| `name` | `name` | Official name, if any | str | – | yes (42,294 null) | blank → null | no | yes |
| `is_potentially_hazardous` | `pha` | JPL PHA flag: Earth MOID ≤ 0.05 au **and** H ≤ 22.0 (CNEOS) | bool | – | yes (126 null) | `Y`→true, `N`→false | **target** | yes |
| `absolute_magnitude_h` | `H` | Absolute magnitude (at 1 au from Sun and observer) | float | mag | yes (2 null) | none | no (defines target) | yes |
| `diameter_km` | `diameter` | Effective body diameter (measured) | float | km | yes (41,232 null) | none | no (size proxy) | yes |
| `albedo` | `albedo` | Geometric albedo | float | – | yes (41,274 null) | none | no (size proxy) | yes |
| `eccentricity` | `e` | Orbital eccentricity | float | – | no | none | **yes** | yes |
| `semi_major_axis_au` | `a` | Semi-major axis | float | au | no | none | **yes** | yes |
| `perihelion_distance_au` | `q` | Perihelion distance (= a(1−e), checked) | float | au | no | none | **yes** | yes |
| `aphelion_distance_au` | `ad` | Aphelion distance (= a(1+e), checked) | float | au | no | none | **yes** | yes |
| `inclination_deg` | `i` | Inclination to the ecliptic | float | deg | no | none | **yes** | yes |
| `ascending_node_deg` | `om` | Longitude of the ascending node | float | deg | no | encoded as sin/cos for ML | **yes** (derived) | yes |
| `argument_of_perihelion_deg` | `w` | Argument of perihelion | float | deg | no | encoded as sin/cos for ML | **yes** (derived) | yes |
| `mean_anomaly_deg` | `ma` | Mean anomaly at the osculation epoch | float | deg | no | none | no (epoch-dependent) | yes |
| `mean_motion_deg_per_day` | `n` | Mean motion | float | deg/day | no | none | no (redundant with a) | yes |
| `orbital_period_days` | `per` | Orbital period | float | days | no | none | no (redundant with a) | yes |
| `earth_moid_au` | `moid` | Minimum distance between the orbits of Earth and the body | float | au | yes (126 null) | none | no (defines target) | yes |
| `epoch_jd` | `epoch` | Epoch of osculation (JD, TDB) | float | JD | no | none | no | yes |
| `condition_code` | `condition_code` | MPC "U" orbit-uncertainty estimate, 0 (good) – 9 (very uncertain) | str | ordinal | yes (2 null) | blank → null | no (post-outcome) | yes |
| `first_obs_date` | `first_obs` | Date of the first observation used in the orbit | str | `YYYY-MM-DD` (may contain `??`) | no | none | no | yes |
| `last_obs_date` | `last_obs` | Date of the last observation used | str | `YYYY-MM-DD` | no | none | no (post-outcome) | yes |
| `first_obs_year` | derived | Year of `first_obs_date` | int | year | no | first 4 digits | **no — chronological split only** | no |
| `n_obs_used` | `n_obs_used` | Observations used in the orbit fit | int | count | no | none | no (post-outcome) | yes |
| `data_arc_days` | `data_arc` | Days spanned by the observations | int | days | yes (430 null) | string → int | no (post-outcome) | yes |
| `rms` | `rms` | Normalised RMS of the orbit fit | float | – | no | none | no | yes |
| `orbit_class` | `class` | Orbit class code (`APO` 24,157; `AMO` 14,823; `ATE` 3,459; `IEO` 38) | str | – | no | none | no (redundant) | yes |

Validation constraints (`ml/validation/schema.py`), applied only where physically or definitionally
valid: `spkid > 0`; `0 ≤ e < 1`; `a > 0`; `0 < q ≤ 1.3` (NEO definition); `0 ≤ i ≤ 180`;
`0 ≤ Ω, ω, M ≤ 360`; `moid ≥ 0`; `diameter > 0`; `albedo ≥ 0`; `q ≈ a(1−e)` and `Q ≈ a(1+e)` within a
relative 1e-4 (observed worst case 1e-7); `pha ∈ {Y, N, null}`; unique `spkid` and `designation`.
There is deliberately **no range check on `H`** (no physical bound applies).

## Close approaches (`close_approaches`, source: CAD API)

| Field (internal) | Source field | Meaning | Type | Unit | Nullable | Transformation | ML? | API? |
|---|---|---|---|---|---|---|---|---|
| `designation` → `neo_id` | `des` | Object designation; joined to `neo_objects.designation` | str | – | no | mapped to SPK-ID | no | as `neo_id` |
| `orbit_id` | `orbit_id` | JPL orbit solution used | str | – | yes | none | no | no |
| `approach_jd` | `jd` | Time of closest approach, Julian date (TDB) | float | JD | no | none | no | no |
| `approach_time_tdb` | `cd` | Same, calendar form `YYYY-Mon-DD HH:MM` (TDB) | datetime | TDB (naive) | no | parsed | no | yes (`date`) |
| `distance_au` | `dist` | Nominal approach distance (centre to centre) | float | au | no | none | no | yes (`miss_distance_au`) |
| `distance_min_au` / `distance_max_au` | `dist_min` / `dist_max` | 3-sigma bounds of the distance | float | au | no | none | no | yes |
| `v_rel_km_s` | `v_rel` | Velocity relative to the body at close approach | float | km/s | no | none | no | yes (`relative_velocity_km_s`) |
| `v_inf_km_s` | `v_inf` | Velocity relative to a massless body | float | km/s | yes (21 null) | none | no | yes |
| `time_uncertainty` | `t_sigma_f` | 3-sigma time uncertainty, JPL format `D_HH:MM`, `HH:MM` or `< 00:01` | str | – | yes | none | no | yes |
| `absolute_magnitude_h` | `h` | Absolute magnitude of the object | float | mag | yes | none | no | no |
| `body` | request parameter | Body approached (`Earth`) | str | – | no | none | no | yes (`orbiting_body`) |

Constraints: distances, velocities ≥ 0; `distance_min ≤ distance ≤ distance_max`; no duplicate
`(designation, jd, body)`; every designation must exist in the validated NEO set.

`miss_distance_km` (API only) = `distance_au × 149,597,870.7` (IAU 2012 definition of the au).

## ML dataset (`data/processed/neo_ml_dataset.csv`)

`spkid, designation, first_obs_year, split, <7 orbital-element inputs>, is_potentially_hazardous (0/1)`.
Only rows with a known target and complete inputs (42,351 of 42,477). See
[`DATA_LEAKAGE.md`](DATA_LEAKAGE.md) for why the other columns are excluded and
[`FEATURE_POLICY.md`](FEATURE_POLICY.md) for the derived features.

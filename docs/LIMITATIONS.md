# Known Limitations

> **Status: DOCUMENTED FROM THE IMPLEMENTATION AND REAL RESULTS (2026-09-21).** Only limitations
> that were observed or verified are listed.

## Scientific framing

* **The target is a deterministic rule.** JPL's PHA flag is "Earth MOID ≤ 0.05 au and H ≤ 22.0"; it
  matches that rule for 42,301 of 42,351 objects. `moid` and `H` are therefore excluded as inputs,
  and the models learn only which *orbits* can approach Earth closely. This is a weaker task than
  reproducing the flag and needs **human confirmation** of the intended scientific goal
  ([`DATA_LEAKAGE.md`](DATA_LEAKAGE.md)).
* **Not an impact-prediction or risk system** ([`SCIENTIFIC_INTEGRITY.md`](SCIENTIFIC_INTEGRITY.md)).
* SHAP values describe how a model uses its inputs. They are not causal statements about asteroids.

## Dataset limitations

* Single snapshot (2026-09-21). Orbits and flags change with new observations; re-ingest to refresh.
* Only objects that have been **discovered** (discovery/observation bias); small and faint objects are
  under-represented.
* SBDB provides no diameter range: `diameter_km` is measured for only 2.9% of objects (albedo 2.8%).
* CAD holds only approaches within 0.05 au of Earth during 2000–2100 (our query), times in TDB, and
  future values are predictions with uncertainty.
* 50 of 42,351 flagged objects disagree with the published PHA rule near H ≈ 22; the cause is unknown.

## Missing-data limitations

126 NEOs have no PHA flag (no MOID) and are excluded from ML but kept in the database/API as
`is_potentially_hazardous: null`. `H` is missing for 2 objects, `data_arc` for 430, `condition_code` for 2.
The seven model inputs have **no** missing values, so no imputation is used; the API rejects incomplete input.

## Temporal limitations

Chronological split by first-observation year (train ≤ 2022, validation 2023–2024, test 2025–2026). The
PHA rate falls from 7.5% to 1.9% to 1.3% because recent discoveries are small; the model cannot see
size, so it cannot adapt. Thresholds tuned on validation are not optimal for test. A random-split
comparison was not run.

## ML limitations

* **Weak classifier.** Best test PR-AUC ≈ 0.15 (no-skill 0.013), precision ≤ 0.14, recall 0.28–0.52.
  `random_forest-v1` flags 211 test objects, 25 of which are PHAs, and misses 39 of 64.
* **Real miss:** Apophis (a PHA with Earth MOID 0.000108 au) is predicted *not* hazardous (probability
  0.176 < threshold 0.270).
* **Small test set:** 64 positives; intervals are wide (test PR-AUC 95% CI for the forest: 0.088–0.236)
  and the six models are statistically indistinguishable on test.
* No hyper-parameter search, no cross-validation, no probability calibration, no ensembling.
* Class-imbalance handling was limited to class weights and a tuned threshold; SMOTE was not tried.
* Every model is `experimental`; none has had expert review.

## Feature limitations

Only the seven orbital elements are used. Physical properties (size, albedo) are excluded on
leakage grounds and are mostly missing anyway. Observation metadata is excluded as post-outcome.

## Model uncertainty

The API returns a probability and a validation-tuned threshold; there is no confidence interval per
prediction. `*_balanced` models output uncalibrated probabilities.

## API / deployment limitations

* The JPL APIs were reachable during development; they can be unavailable — ingestion then fails
  explicitly, and the deployed app serves whatever is already in its database (no fallback data).
* No authentication; the rate limiter is per process ([`SECURITY.md`](SECURITY.md)).
* Model binaries are **not in Git** (`*.joblib` ignored; the random forests are 47–53 MB). A deployment
  must build or supply `ml/artifacts/` and run `python -m app.cli sync-models`.
* First prediction per model takes ~1.5 s (model load + SHAP explainer), later ones are fast.
* Deployment (Render/Vercel) is **not implemented or verified**.

## Environment note (development machine)

Docker's Postgres uses host port 55432 (`POSTGRES_HOST_PORT`) because a separate PostgreSQL already
occupied 5432. On Windows use `127.0.0.1`, not `localhost`, in `DATABASE_URL` (IPv6 attempt adds ~8 s).

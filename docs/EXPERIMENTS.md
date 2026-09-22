# Experiments Log

> **Status: 6 experiments run on real JPL data** — dataset `jpl-sbdb-neo-20260921-c34b5103`,
> features `features-v1`, chronological split (train ≤ 2022, validation 2023–2024, test 2025–2026),
> seed 42. Full per-experiment entries are appended **automatically** below by
> `python -m ml.evaluation`; every value is computed, none typed by hand.

## Summary (validation used for selection; test evaluated afterwards)

Prevalence (= no-skill PR-AUC): validation 0.0195, test 0.0128 (64 positives). Threshold = max-F1 on validation.

| Model | Thr. | Val PR-AUC | Val ROC-AUC | Val F1 | Test PR-AUC (95% CI) | Test ROC-AUC (95% CI) | Test prec. | Test recall | Test F1 |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|
| `logistic_regression-v1` | 0.128 | 0.079 | 0.830 | 0.147 | 0.052 (0.033–0.088) | 0.806 (0.762–0.850) | 0.043 | 0.297 | 0.075 |
| `logistic_regression_balanced-v1` | 0.704 | 0.077 | 0.834 | 0.141 | 0.058 (0.034–0.108) | 0.811 (0.769–0.852) | 0.046 | 0.281 | 0.079 |
| **`random_forest-v1`** | 0.270 | **0.183** | **0.900** | **0.290** | 0.146 (0.088–0.236) | 0.898 (0.867–0.926) | 0.118 | 0.391 | 0.182 |
| `random_forest_balanced-v1` | 0.599 | 0.145 | 0.892 | 0.236 | 0.121 (0.080–0.204) | 0.896 (0.868–0.924) | 0.105 | 0.516 | 0.175 |
| `xgboost-v1` | 0.324 | 0.145 | 0.883 | 0.247 | 0.152 (0.089–0.246) | 0.878 (0.846–0.910) | 0.139 | 0.375 | 0.203 |
| `xgboost_balanced-v1` | 0.722 | 0.113 | 0.857 | 0.189 | 0.137 (0.082–0.247) | 0.873 (0.841–0.905) | 0.097 | 0.422 | 0.157 |

## Observations

* **Best on validation: `random_forest-v1`** (PR-AUC 0.183). On test XGBoost's PR-AUC (0.152) is
  nominally higher than the forest's (0.146), but the intervals overlap almost completely; with 64
  test positives the two are **statistically indistinguishable**. Selection was not changed by the
  test result.
* **Every model beats chance** (test PR-AUC 4–12× the 0.0128 prevalence; ROC-AUC 0.81–0.90) yet is a
  **weak classifier**: the best test precision is 0.14 and recall 0.28–0.52. Orbital elements carry
  real signal about the MOID half of the PHA rule; the H half is invisible to them.
* **Tree ensembles clearly beat logistic regression** (validation and test PR-AUC roughly 2–3×),
  consistent with a non-linear relationship between orbit shape and closeness to Earth's orbit.
* **Class weighting did not help ranking.** For every algorithm the balanced variant had equal or
  lower validation PR-AUC; it trades precision for recall at its own threshold (e.g. random forest
  test recall 0.391 → 0.516, precision 0.118 → 0.105).
* **Distribution shift dominates.** Positive rate falls from 7.5% (train) to 1.9% (validation) and
  1.3% (test); thresholds tuned on validation are not optimal for test.
* SHAP: all models rank `perihelion_distance_au` first, then `eccentricity` and `inclination_deg`
  (see `ml/artifacts/*/v1/shap_global.json`).

## Limitations

Fixed default hyper-parameters (no search); single chronological split (no cross-validation);
small test set; no calibration; `H`/`moid` excluded by design (see `DATA_LEAKAGE.md`); results apply
to this snapshot only. A random-split comparison was not run.

## Decision

All six models remain **`experimental`**; none is promoted. `random_forest-v1` is served by default
because it is best on validation PR-AUC (rule: status first, then validation PR-AUC). Promotion to
`validated`/`production` requires human/scientific review (`python -m app.cli set-status`).

---

## Distribution shift investigation

> Reproducible via `python -m ml.diagnostics.distribution_shift`; full output
> `ml/diagnostics/output/distribution_shift.json`. Read-only: it does not retrain or re-split
> anything (`ml.training`/`ml.preprocessing`/`ml.features` are unchanged).

**Established (directly measured):**

* PHA prevalence falls monotonically: train 7.52% → validation 1.95% → test 1.28% (unchanged from
  above; this is the same split, not recomputed).
* Orbit-class composition and prevalence both shift. Apollo (APO), the largest class, alone drops
  from 11.48% PHA (train, n=17,645) to 3.05% (validation, n=3,442) to 1.87% (test, n=2,998); Amor
  (AMO) drops from 1.29% to 0.32% to 0.13%. Aten (ATE) and Atira (IEO) are far smaller
  (train n=2,463 and n=32) and noisier — see the full table in the JSON output.
* A train-vs-test two-sample Kolmogorov–Smirnov test on each raw orbital feature rejects the
  "same distribution" null hypothesis (p < 1e-6) for 6 of 7 features — `semi_major_axis_au`
  (D=0.065, p=3.4e-16), `eccentricity` (D=0.057, p=1.4e-12), `inclination_deg` (D=0.049,
  p=2.5e-9), `perihelion_distance_au` (D=0.069, p=3.8e-18), `aphelion_distance_au` (D=0.064,
  p=9.0e-16), `ascending_node_deg` (D=0.043, p=1.7e-7). `argument_of_perihelion_deg` is the one
  exception: D=0.015, p=0.283 — **not** significantly different between train and test.
* Prevalence-by-discovery-year (full series in the JSON) declines steadily from the 1990s–2000s
  (commonly 15–30% in years with meaningful sample size) down to 2.8% (2018), 1.3–1.9% (2020–2026)
  — consistent with the split-level numbers, not an artefact of the split boundaries.

**INCONCLUSIVE:** the root cause of the prevalence shift — why recent discoveries skew toward
smaller (non-PHA, H > 22) objects — cannot be established from this dataset alone. It would
require survey completeness / discovery-effort data (e.g. per-survey magnitude limits over time)
that is not part of the SBDB snapshot used here. We record that recent objects are measurably
different (orbit-class mix, per-feature KS tests) without claiming to know *why* discovery
composition changed.

## Experiment 2: Subgroup / orbital-class evaluation

> Reproducible via `python -m ml.diagnostics.subgroup`; full output
> `ml/diagnostics/output/subgroup_evaluation.json`. Evaluates the served default model
> (`random_forest-v1`) read-only, grouped by CNEOS orbital class (SBDB `class`: `IEO`=Atira,
> `ATE`=Aten, `APO`=Apollo, `AMO`=Amor — the classification JPL already computes, not re-derived
> here). A subgroup with fewer than 10 positives in a split reports `INSUFFICIENT SAMPLE` instead
> of a misleading metric; support/positives/prevalence are always reported.

| Split | Orbit class | Support | Positives | Prevalence | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | **Apollo** | 3,442 | 105 | 3.05% | 0.215 | 0.476 | 0.296 | 0.190 | 0.864 |
| validation | Amor | 1,851 | 6 | 0.32% | INSUFFICIENT SAMPLE | | | | |
| validation | Aten | 495 | 2 | 0.40% | INSUFFICIENT SAMPLE | | | | |
| validation | Atira | 2 | 0 | 0% | INSUFFICIENT SAMPLE | | | | |
| test | **Apollo** | 2,998 | 56 | 1.87% | 0.128 | 0.446 | 0.199 | 0.166 | 0.876 |
| test | Amor | 1,530 | 2 | 0.13% | INSUFFICIENT SAMPLE | | | | |
| test | Aten | 484 | 5 | 1.03% | INSUFFICIENT SAMPLE | | | | |
| test | Atira | 4 | 1 | 25% | INSUFFICIENT SAMPLE | | | | |

**Observation:** only Apollo has enough positives (≥10) in both splits for a meaningful
per-subgroup metric. Its test PR-AUC (0.166) and ROC-AUC (0.876) are close to the overall test
figures (0.146 / 0.898) — the model's aggregate performance is not being propped up or masked by
one dominant subgroup, but this conclusion applies only to Apollo; Amor, Aten and Atira remain
**INSUFFICIENT SAMPLE** and no claim is made about them individually. Atira (32 objects total in
the whole dataset) is too small to evaluate at all; its very small counts even in the composition
table (train 7/32 positive, test 1/4) should not be read as a reliable prevalence estimate.

## Experiment 3: Calibration diagnostic

> Reproducible via `python -m ml.diagnostics.calibration`; full output
> `ml/diagnostics/output/calibration.json`. Evaluated on **validation**, not test: test is
> reserved for the single final evaluation per model (`docs/ML_WORKFLOW.md`); validation is
> already reused for threshold tuning, and reusing it again for this non-selective diagnostic
> (it does not choose between models or feed back into training) adds no new leakage. This
> project has no separate calibration split. No calibration transform is fit or applied to the
> served model — this is read-only.

| Metric | Value |
|---|---:|
| Brier score (`random_forest-v1`, validation, n=5,790) | 0.0234 |
| No-skill Brier score (predict the validation prevalence for everyone) | 0.0191 |

**The model's Brier score is *worse* than the no-skill baseline.** Predicting the constant base
rate (1.95%) for every object minimises squared error better than the model's actual scores do.
This is compatible with good *ranking* (ROC-AUC 0.90, PR-AUC 0.18 ≫ no-skill 0.0195) alongside
poor *calibration*: reliability-curve bins (`strategy="quantile"`, 10 bins) show the model is
overconfident in its highest-scoring bin — mean predicted probability 27.9% in that bin, observed
frequency only 13.0% — and near-zero observed frequency in several low/mid bins whose mean
predicted probability is 1–6%. **Conclusion: `random_forest-v1`'s output is not demonstrated to
be a calibrated probability.** It is useful for ranking objects relative to each other, not for
reading as "this object has an X% chance of being a PHA." See the terminology change in
`docs/API_CONTRACT.md` and the frontend ("Model Score", not "Probability").

## Experiment 4: Definition-reconstruction diagnostic

> **NOT a predictive model. Not used for production, the default model, dashboard predictions,
> or model selection.** Reproducible via `python -m ml.diagnostics.definition_reconstruction`;
> full output `ml/diagnostics/output/definition_reconstruction.json`. Artifacts are saved under
> `ml/diagnostics/artifacts/` (never `ml/artifacts/`) with `feature_version
> "features-diagnostic-definition-v1"`, so `python -m app.cli sync-models` cannot register them
> and `ml.inference.predict.load_model` would refuse them even if misdirected there — see
> `tests/ml/test_diagnostics.py`.

Same chronological split, same algorithms (class_weight=`none` only — the balanced sweep is
skipped as unnecessary for this comparison), but with `absolute_magnitude_h` and `earth_moid_au`
added to the orbital-only feature set (2 of 42,351 rows dropped for missing H/MOID).

| Algorithm | Test PR-AUC (primary, orbital-only) | Test PR-AUC (+ H, MOID) | Test recall (+ H, MOID) | Test precision (+ H, MOID) |
|---|---:|---:|---:|---:|
| Logistic regression | 0.052 | 0.736 | 0.563 | 0.766 |
| Random forest | 0.146 | 0.992 | 1.000 | 0.941 |
| XGBoost | 0.152 | 0.997 | 1.000 | 0.970 |

**Interpretation:** giving the model direct access to the two variables that *define* the JPL PHA
rule makes the task almost trivial for tree ensembles (test PR-AUC 0.99+, recall 1.00) and much
easier even for plain logistic regression (0.052 → 0.736). This demonstrates the gap between
*reconstructing JPL's definition* (near-perfect, once H/MOID are visible) and *learning orbital-
geometry signal without them* (Experiment 1, PR-AUC 0.05–0.18) — exactly the distinction
`docs/DATA_LEAKAGE.md` uses to justify excluding H/MOID from the primary model.

---

## Experiment Template

```
Experiment ID:
Date:
Dataset version:
Feature version:
Model:
Parameters:
Training split:
Validation split:
Test split:

Accuracy:
Precision:
Recall:
F1:
ROC-AUC:
PR-AUC:

Observations:
Limitations:
Decision:
```

---

## Experiment Log

Entries are appended by `python -m ml.evaluation` (idempotent per experiment ID). To add a new
experiment: `python -m ml.training` (creates the next version) then `python -m ml.evaluation`.

<!-- experiment-log-entries -->

### EXP-20260921T130452Z-logistic_regression-v1

```
Experiment ID: EXP-20260921T130452Z-logistic_regression-v1
Date: 2026-09-21T13:04:52.355298+00:00
Dataset version: jpl-sbdb-neo-20260921-c34b5103
Feature version: features-v1
Model: logistic_regression-v1 (logistic_regression, class_weight=none)
Parameters: {"C": 1.0, "dual": false, "fit_intercept": true, "intercept_scaling": 1, "l1_ratio": 0.0, "max_iter": 2000, "penalty": "deprecated", "random_state": 42, "solver": "lbfgs", "tol": 0.0001, "verbose": 0, "warm_start": false}
Random seed: 42
Training split: 31545 rows, 2372 positives (7.52%), first_obs_year 1893-2022
Validation split: 5790 rows, 113 positives (1.95%), first_obs_year 2023-2024
Test split: 5016 rows, 64 positives (1.28%), first_obs_year 2025-2026
Decision threshold: 0.1281 (maximises F1 on the validation split)
Status: experimental
```

| Metric | Validation | Test |
|--------|-----------:|-----:|
| Accuracy | 0.9057 | 0.9071 |
| Precision | 0.0892 | 0.0432 |
| Recall | 0.4159 | 0.2969 |
| F1 | 0.1469 | 0.0754 |
| ROC-AUC | 0.8304 | 0.8062 |
| PR-AUC | 0.0793 | 0.0522 |

- No-skill PR-AUC (prevalence): validation 0.0195, test 0.0128
- Test 95% bootstrap CI (1000 resamples): ROC-AUC [0.7620, 0.8500], PR-AUC [0.0332, 0.0881]
- Test confusion matrix: TN=4531 FP=421 FN=45 TP=19

### EXP-20260921T130452Z-logistic_regression_balanced-v1

```
Experiment ID: EXP-20260921T130452Z-logistic_regression_balanced-v1
Date: 2026-09-21T13:04:52.420538+00:00
Dataset version: jpl-sbdb-neo-20260921-c34b5103
Feature version: features-v1
Model: logistic_regression_balanced-v1 (logistic_regression, class_weight=balanced)
Parameters: {"C": 1.0, "class_weight": "balanced", "dual": false, "fit_intercept": true, "intercept_scaling": 1, "l1_ratio": 0.0, "max_iter": 2000, "penalty": "deprecated", "random_state": 42, "solver": "lbfgs", "tol": 0.0001, "verbose": 0, "warm_start": false}
Random seed: 42
Training split: 31545 rows, 2372 positives (7.52%), first_obs_year 1893-2022
Validation split: 5790 rows, 113 positives (1.95%), first_obs_year 2023-2024
Test split: 5016 rows, 64 positives (1.28%), first_obs_year 2025-2026
Decision threshold: 0.7039 (maximises F1 on the validation split)
Status: experimental
```

| Metric | Validation | Test |
|--------|-----------:|-----:|
| Accuracy | 0.9155 | 0.9169 |
| Precision | 0.0877 | 0.0463 |
| Recall | 0.3540 | 0.2812 |
| F1 | 0.1406 | 0.0795 |
| ROC-AUC | 0.8335 | 0.8109 |
| PR-AUC | 0.0769 | 0.0575 |

- No-skill PR-AUC (prevalence): validation 0.0195, test 0.0128
- Test 95% bootstrap CI (1000 resamples): ROC-AUC [0.7695, 0.8523], PR-AUC [0.0340, 0.1078]
- Test confusion matrix: TN=4581 FP=371 FN=46 TP=18

### EXP-20260921T130454Z-random_forest-v1

```
Experiment ID: EXP-20260921T130454Z-random_forest-v1
Date: 2026-09-21T13:04:54.214012+00:00
Dataset version: jpl-sbdb-neo-20260921-c34b5103
Feature version: features-v1
Model: random_forest-v1 (random_forest, class_weight=none)
Parameters: {"bootstrap": true, "ccp_alpha": 0.0, "criterion": "gini", "max_features": "sqrt", "min_impurity_decrease": 0.0, "min_samples_leaf": 5, "min_samples_split": 2, "min_weight_fraction_leaf": 0.0, "n_estimators": 300, "n_jobs": -1, "oob_score": false, "random_state": 42, "verbose": 0, "warm_start": false}
Random seed: 42
Training split: 31545 rows, 2372 positives (7.52%), first_obs_year 1893-2022
Validation split: 5790 rows, 113 positives (1.95%), first_obs_year 2023-2024
Test split: 5016 rows, 64 positives (1.28%), first_obs_year 2025-2026
Decision threshold: 0.2703 (maximises F1 on the validation split)
Status: experimental
```

| Metric | Validation | Test |
|--------|-----------:|-----:|
| Accuracy | 0.9560 | 0.9551 |
| Precision | 0.2114 | 0.1185 |
| Recall | 0.4602 | 0.3906 |
| F1 | 0.2897 | 0.1818 |
| ROC-AUC | 0.9003 | 0.8978 |
| PR-AUC | 0.1827 | 0.1461 |

- No-skill PR-AUC (prevalence): validation 0.0195, test 0.0128
- Test 95% bootstrap CI (1000 resamples): ROC-AUC [0.8668, 0.9255], PR-AUC [0.0881, 0.2362]
- Test confusion matrix: TN=4766 FP=186 FN=39 TP=25

### EXP-20260921T130455Z-random_forest_balanced-v1

```
Experiment ID: EXP-20260921T130455Z-random_forest_balanced-v1
Date: 2026-09-21T13:04:55.819810+00:00
Dataset version: jpl-sbdb-neo-20260921-c34b5103
Feature version: features-v1
Model: random_forest_balanced-v1 (random_forest, class_weight=balanced)
Parameters: {"bootstrap": true, "ccp_alpha": 0.0, "class_weight": "balanced", "criterion": "gini", "max_features": "sqrt", "min_impurity_decrease": 0.0, "min_samples_leaf": 5, "min_samples_split": 2, "min_weight_fraction_leaf": 0.0, "n_estimators": 300, "n_jobs": -1, "oob_score": false, "random_state": 42, "verbose": 0, "warm_start": false}
Random seed: 42
Training split: 31545 rows, 2372 positives (7.52%), first_obs_year 1893-2022
Validation split: 5790 rows, 113 positives (1.95%), first_obs_year 2023-2024
Test split: 5016 rows, 64 positives (1.28%), first_obs_year 2025-2026
Decision threshold: 0.5989 (maximises F1 on the validation split)
Status: experimental
```

| Metric | Validation | Test |
|--------|-----------:|-----:|
| Accuracy | 0.9373 | 0.9378 |
| Precision | 0.1547 | 0.1051 |
| Recall | 0.4956 | 0.5156 |
| F1 | 0.2358 | 0.1746 |
| ROC-AUC | 0.8924 | 0.8963 |
| PR-AUC | 0.1449 | 0.1206 |

- No-skill PR-AUC (prevalence): validation 0.0195, test 0.0128
- Test 95% bootstrap CI (1000 resamples): ROC-AUC [0.8675, 0.9237], PR-AUC [0.0799, 0.2038]
- Test confusion matrix: TN=4671 FP=281 FN=31 TP=33

### EXP-20260921T130458Z-xgboost-v1

```
Experiment ID: EXP-20260921T130458Z-xgboost-v1
Date: 2026-09-21T13:04:58.858168+00:00
Dataset version: jpl-sbdb-neo-20260921-c34b5103
Feature version: features-v1
Model: xgboost-v1 (xgboost, class_weight=none)
Parameters: {"colsample_bytree": 0.8, "enable_categorical": true, "eval_metric": "aucpr", "learning_rate": 0.1, "max_depth": 6, "missing": "nan", "n_estimators": 300, "n_jobs": -1, "objective": "binary:logistic", "random_state": 42, "scale_pos_weight": 1.0, "subsample": 0.8, "tree_method": "hist"}
Random seed: 42
Training split: 31545 rows, 2372 positives (7.52%), first_obs_year 1893-2022
Validation split: 5790 rows, 113 positives (1.95%), first_obs_year 2023-2024
Test split: 5016 rows, 64 positives (1.28%), first_obs_year 2025-2026
Decision threshold: 0.3245 (maximises F1 on the validation split)
Status: experimental
```

| Metric | Validation | Test |
|--------|-----------:|-----:|
| Accuracy | 0.9579 | 0.9623 |
| Precision | 0.1896 | 0.1387 |
| Recall | 0.3540 | 0.3750 |
| F1 | 0.2469 | 0.2025 |
| ROC-AUC | 0.8834 | 0.8777 |
| PR-AUC | 0.1450 | 0.1522 |

- No-skill PR-AUC (prevalence): validation 0.0195, test 0.0128
- Test 95% bootstrap CI (1000 resamples): ROC-AUC [0.8457, 0.9099], PR-AUC [0.0885, 0.2457]
- Test confusion matrix: TN=4803 FP=149 FN=40 TP=24

### EXP-20260921T130459Z-xgboost_balanced-v1

```
Experiment ID: EXP-20260921T130459Z-xgboost_balanced-v1
Date: 2026-09-21T13:04:59.507889+00:00
Dataset version: jpl-sbdb-neo-20260921-c34b5103
Feature version: features-v1
Model: xgboost_balanced-v1 (xgboost, class_weight=balanced)
Parameters: {"colsample_bytree": 0.8, "enable_categorical": true, "eval_metric": "aucpr", "learning_rate": 0.1, "max_depth": 6, "missing": "nan", "n_estimators": 300, "n_jobs": -1, "objective": "binary:logistic", "random_state": 42, "scale_pos_weight": 12.298903878583474, "subsample": 0.8, "tree_method": "hist"}
Random seed: 42
Training split: 31545 rows, 2372 positives (7.52%), first_obs_year 1893-2022
Validation split: 5790 rows, 113 positives (1.95%), first_obs_year 2023-2024
Test split: 5016 rows, 64 positives (1.28%), first_obs_year 2025-2026
Decision threshold: 0.7221 (maximises F1 on the validation split)
Status: experimental
```

| Metric | Validation | Test |
|--------|-----------:|-----:|
| Accuracy | 0.9390 | 0.9424 |
| Precision | 0.1273 | 0.0968 |
| Recall | 0.3628 | 0.4219 |
| F1 | 0.1885 | 0.1574 |
| ROC-AUC | 0.8572 | 0.8728 |
| PR-AUC | 0.1129 | 0.1371 |

- No-skill PR-AUC (prevalence): validation 0.0195, test 0.0128
- Test 95% bootstrap CI (1000 resamples): ROC-AUC [0.8409, 0.9053], PR-AUC [0.0817, 0.2469]
- Test confusion matrix: TN=4700 FP=252 FN=37 TP=27

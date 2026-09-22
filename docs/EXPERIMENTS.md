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

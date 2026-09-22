# ML Workflow

> **Status: IMPLEMENTED.** Six models were trained and evaluated on real JPL data (dataset
> `jpl-sbdb-neo-20260921-c34b5103`). Results: [`EXPERIMENTS.md`](EXPERIMENTS.md); model
> description: [`MODEL_CARD.md`](MODEL_CARD.md). No model is `production`; all are `experimental`.

## Task and target

Binary classification of JPL's **`pha` flag** ("potentially hazardous asteroid") for near-Earth
asteroids, from orbital elements only. Definition and source: CNEOS — Earth MOID ≤ 0.05 au **and**
H ≤ 22.0 ([`DATA_SOURCE.md`](DATA_SOURCE.md)). Because the label is a rule over `moid` and `H`, those
are excluded as inputs; see the flagged scientific ambiguity in [`DATA_LEAKAGE.md`](DATA_LEAKAGE.md).
This is **not** an impact-prediction system.

Class distribution (measured): 2,549 positive / 39,802 negative = **6.02% positive** overall — real
imbalance, and it changes over time (7.5% train → 1.3% test).

## Process

```
Real data -> validation -> ML dataset (eligible rows, de-duplicated)
  -> chronological split by first-observation year (train <= 2022 < validation <= 2024 < test)
  -> Pipeline[ build_features -> (StandardScaler for LR) -> classifier ]  fitted on TRAIN only
  -> decision threshold = argmax F1 on VALIDATION
  -> versioned artifact (experimental)
  -> held-out TEST evaluation, once, for every candidate (python -m ml.evaluation)
  -> SHAP (global on validation; local per prediction)
  -> registry (database) -> Inference API
```

## Models

| Model | Library | Fixed parameters (no hyper-parameter search) |
|---|---|---|
| Logistic Regression (baseline) | scikit-learn | `C=1.0`, `max_iter=2000`, standardised inputs |
| Random Forest | scikit-learn | `n_estimators=300`, `min_samples_leaf=5`, `max_features="sqrt"` |
| XGBoost | xgboost | `n_estimators=300`, `max_depth=6`, `learning_rate=0.1`, `subsample=0.8`, `colsample_bytree=0.8`, `tree_method="hist"` |

Seed 42 everywhere. LightGBM was **not** added (no demonstrated need; it would be another
dependency). No neural networks. XGBoost was compared objectively and is *not* the validation winner.

## Class imbalance

Measured first (above). Two treatments were evaluated per algorithm and both are kept:

* `none` — default weighting (probabilities stay close to calibrated);
* `balanced` — `class_weight="balanced"` (LR/RF) or `scale_pos_weight = n_neg/n_pos` (XGBoost).

Both use a validation-tuned probability threshold. SMOTE was **not** used (extra dependency, and
synthetic minority samples in orbital-element space are hard to justify physically). Result: class
weighting raised recall but lowered precision and did **not** improve PR-AUC for any model.
Note `balanced` models' probabilities are not calibrated posteriors.

## Evaluation

Metrics: accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, ROC and PR curve points,
plus 95% bootstrap intervals for ROC-AUC/PR-AUC (1,000 resamples). Accuracy is reported for
completeness but is **misleading** here: predicting "not PHA" for everything scores 98.7% on test.
PR-AUC is compared against the no-skill level (= prevalence: 1.95% validation, 1.28% test).

Model selection uses **validation PR-AUC**; the default served model follows the same rule
(status first, then validation PR-AUC). Test metrics are informational and were computed after
selection. The test set has only 64 positives — differences of a few hundredths are within noise.

## Explainability

SHAP (`TreeExplainer` for RF/XGBoost, `LinearExplainer` for LR). Verified: contributions add up to
the model output (max error 2e-7). Units: log-odds (LR, XGBoost), probability (RF). SHAP describes
*model behaviour*, **not** causal facts about asteroids. Across all models the largest global
attribution is `perihelion_distance_au`, then `eccentricity` and `inclination_deg`.

## Artifacts and registry

`ml/artifacts/<name>/v<N>/`: `model.joblib` (git-ignored, up to 53 MB), `metadata.json`
(parameters, features, versions, split, threshold, metrics, library versions),
`evaluation.json` (curves, bootstrap CIs), `shap_global.json`. Versions are immutable: retraining
creates `v2`. Naming: `xgboost-v1`, `random_forest_balanced-v1`, …

The database `models` table is the registry: `version, name, artifact_path, dataset_version,
feature_version, metrics, status, created_at`. Statuses: `experimental` (all trained models),
`validated`, `production`, `deprecated`. **Nothing is promoted automatically**; a human runs
`python -m app.cli set-status <version> <status>`.

## Reproducibility

Fixed seed, pinned dependencies (`backend/requirements.txt`), recorded library versions, dataset and
feature versions, and a test that retraining yields the same predictions (a parallel forest may
differ at 1 ulp ≈ 3e-16 from float summation order).

"""Definition-reconstruction diagnostic (docs/EXPERIMENTS.md "Experiment 4").

NOT a predictive model. Adds absolute_magnitude_h and earth_moid_au — the two variables that
define the JPL PHA label (docs/DATA_LEAKAGE.md) — to the feature set, to measure how much of the
classification task becomes trivial once the label-defining variables are available, for
comparison against the orbital-only primary experiment. Never used for production, default-model
selection, or the /predict API.

Isolation from the production registry (two independent guards):
  1. Artifacts are saved under ml/diagnostics/artifacts/, never under ml.config.ARTIFACTS_DIR
     (ml/artifacts/). `python -m app.cli sync-models` only scans ml.config.ARTIFACTS_DIR
     (ml.artifacts.list_artifacts), so it can never see these.
  2. feature_version is set to a value ("features-diagnostic-definition-v1") the production code
     does not recognise, so ml.inference.predict.load_model refuses it even if misdirected here.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from xgboost import XGBClassifier

from ml import artifacts, config
from ml.diagnostics import _common
from ml.evaluation import metrics
from ml.features.engineering import build_features
from ml.preprocessing import dataset as ds

OUTPUT_FILE = _common.OUTPUT_DIR / "definition_reconstruction.json"
FEATURE_VERSION = "features-diagnostic-definition-v1"
EXTRA_RAW_FEATURES = ("absolute_magnitude_h", "earth_moid_au")
ALGORITHMS = ("logistic_regression", "random_forest", "xgboost")


def _extended_features(raw: pd.DataFrame) -> pd.DataFrame:
    base = build_features(raw)
    extra = raw[list(EXTRA_RAW_FEATURES)].astype(float).reset_index(drop=True)
    return pd.concat([base.reset_index(drop=True), extra], axis=1)


def _make_pipeline(algorithm: str) -> Pipeline:
    seed = config.RANDOM_SEED
    estimator: Any
    if algorithm == "logistic_regression":
        estimator = LogisticRegression(C=1.0, max_iter=2000, random_state=seed)
    elif algorithm == "random_forest":
        estimator = RandomForestClassifier(
            n_estimators=300, min_samples_leaf=5, n_jobs=-1, random_state=seed)
    elif algorithm == "xgboost":
        estimator = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
            colsample_bytree=0.8, eval_metric="aucpr", tree_method="hist", n_jobs=-1,
            random_state=seed)
    else:
        raise ValueError(f"unknown algorithm: {algorithm!r}")
    steps: list[tuple[str, Any]] = [("features", FunctionTransformer(_extended_features))]
    if algorithm == "logistic_regression":
        steps.append(("scale", StandardScaler()))
    steps.append(("model", estimator))
    return Pipeline(steps)


def _train_one(
    algorithm: str, data: pd.DataFrame, manifest: dict[str, Any], artifacts_root: Path,
    n_dropped: int,
) -> dict[str, Any]:
    raw_features = list(config.RAW_FEATURES) + list(EXTRA_RAW_FEATURES)
    train_part, val_part, test_part = (data[data["split"] == s] for s in ds.SPLITS)
    X_train, y_train = train_part[raw_features], train_part[config.TARGET].to_numpy()
    X_val, y_val = val_part[raw_features], val_part[config.TARGET].to_numpy()
    X_test, y_test = test_part[raw_features], test_part[config.TARGET].to_numpy()

    pipeline = _make_pipeline(algorithm)
    pipeline.fit(X_train, y_train)

    proba_val = pipeline.predict_proba(X_val)[:, 1]
    threshold = metrics.best_f1_threshold(y_val, proba_val)
    val_metrics = metrics.compute_metrics(y_val, proba_val, threshold)

    proba_test = pipeline.predict_proba(X_test)[:, 1]
    test_metrics = metrics.compute_metrics(y_test, proba_test, threshold)
    test_ci = metrics.bootstrap_ci(y_test, proba_test)

    number = artifacts.next_version_number(algorithm, artifacts_root)
    version = f"{algorithm}-diagnostic-defn-recon-v{number}"
    created = datetime.now(UTC)
    metadata: dict[str, Any] = {
        "diagnostic": "definition_reconstruction",
        "NOT_A_PREDICTIVE_MODEL": True,
        "excluded_from_production_selection": True,
        "model_name": algorithm,
        "model_version": version,
        "algorithm": algorithm,
        "class_weight": "none",
        "status": "diagnostic",
        "created_at": created.isoformat(),
        "dataset_version": manifest["dataset_version"],
        "feature_version": FEATURE_VERSION,
        "target": config.TARGET,
        "raw_features": raw_features,
        "random_seed": config.RANDOM_SEED,
        "threshold": threshold,
        "threshold_selection": "maximises F1 on the validation split",
        "rows_dropped_missing_h_or_moid": n_dropped,
        "metrics": {"validation": val_metrics, "test": {**test_metrics, "bootstrap_ci": test_ci}},
        "libraries": artifacts.library_versions(),
    }
    directory = artifacts.artifact_dir(algorithm, number, artifacts_root)
    artifacts.save_artifact(directory, pipeline, metadata)
    return metadata


def run(
    processed_dir: Path | None = None,
    interim_dir: Path | None = None,
    artifacts_root: Path | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    artifacts_root = artifacts_root or _common.ARTIFACTS_DIR
    manifest = ds.load_manifest(processed_dir)
    data = ds.load_dataset(processed_dir)
    data, n_dropped = _common.with_interim_columns(
        data, interim_dir, columns=EXTRA_RAW_FEATURES, on_missing="drop")

    results = {a: _train_one(a, data, manifest, artifacts_root, n_dropped) for a in ALGORITHMS}

    report: dict[str, Any] = {
        "diagnostic": "definition_reconstruction",
        "generated_at": datetime.now(UTC).isoformat(),
        "NOT_A_PREDICTIVE_MODEL": True,
        "excluded_from_production_selection": True,
        "purpose": (
            "Measures how much of the PHA classification task becomes trivial when the two "
            "label-defining variables (H, Earth MOID) are available as inputs, for comparison "
            "against the orbital-only primary experiment (docs/EXPERIMENTS.md Experiment 1)."
        ),
        "dataset_version": manifest["dataset_version"],
        "feature_version": FEATURE_VERSION,
        "raw_features": list(config.RAW_FEATURES) + list(EXTRA_RAW_FEATURES),
        "rows_dropped_missing_h_or_moid": n_dropped,
        "algorithms": results,
        "artifact_root": str(artifacts_root),
        "artifact_root_isolated_from_production": str(artifacts_root) != str(config.ARTIFACTS_DIR),
        "libraries": artifacts.library_versions(),
    }
    out = output_file or OUTPUT_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(artifacts.dumps_strict(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        run()
    except FileNotFoundError as exc:
        print(f"DEFINITION-RECONSTRUCTION DIAGNOSTIC FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"wrote {OUTPUT_FILE}")

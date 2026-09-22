"""Model training.

Protocol (see docs/ML_WORKFLOW.md):
  * fit only on the ``train`` split; preprocessing lives inside the sklearn Pipeline;
  * choose the decision threshold on the ``validation`` split (max F1);
  * the ``test`` split is untouched here; it is evaluated once by ``python -m ml.evaluation``.
No hyper-parameter search is performed: parameters are fixed, documented defaults.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from xgboost import XGBClassifier

from ml import artifacts, config
from ml.evaluation import metrics
from ml.features.engineering import build_features
from ml.preprocessing import dataset as ds

ALGORITHMS = ("logistic_regression", "random_forest", "xgboost")
CLASS_WEIGHTS = ("none", "balanced")


def make_pipeline(algorithm: str, class_weight: str, y_train: np.ndarray) -> Pipeline:
    """Feature engineering -> (scaling for LR) -> classifier. Fitted on train data only."""
    seed = config.RANDOM_SEED
    balanced = class_weight == "balanced"
    if algorithm == "logistic_regression":
        estimator: Any = LogisticRegression(
            C=1.0, max_iter=2000, class_weight="balanced" if balanced else None,
            random_state=seed)
    elif algorithm == "random_forest":
        estimator = RandomForestClassifier(
            n_estimators=300, min_samples_leaf=5, n_jobs=-1,
            class_weight="balanced" if balanced else None, random_state=seed)
    elif algorithm == "xgboost":
        n_pos = int(np.sum(y_train))
        estimator = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
            colsample_bytree=0.8, eval_metric="aucpr", tree_method="hist", n_jobs=-1,
            random_state=seed,
            scale_pos_weight=(len(y_train) - n_pos) / n_pos if balanced else 1.0)
    else:
        raise ValueError(f"unknown algorithm: {algorithm!r}")
    steps: list[tuple[str, Any]] = [("features", FunctionTransformer(build_features))]
    if algorithm == "logistic_regression":
        steps.append(("scale", StandardScaler()))
    steps.append(("model", estimator))
    return Pipeline(steps)


def model_name(algorithm: str, class_weight: str) -> str:
    return algorithm if class_weight == "none" else f"{algorithm}_{class_weight}"


def split_xy(data: pd.DataFrame, split: str) -> tuple[pd.DataFrame, np.ndarray]:
    part = data[data["split"] == split]
    return part[config.RAW_FEATURES], part[config.TARGET].to_numpy()


def train_one(
    algorithm: str,
    class_weight: str,
    data: pd.DataFrame,
    manifest: dict[str, Any],
    artifacts_root: Path | None = None,
) -> dict[str, Any]:
    X_train, y_train = split_xy(data, "train")
    X_val, y_val = split_xy(data, "validation")

    pipeline = make_pipeline(algorithm, class_weight, y_train)
    pipeline.fit(X_train, y_train)

    proba_val = pipeline.predict_proba(X_val)[:, 1]
    threshold = metrics.best_f1_threshold(y_val, proba_val)
    val_metrics = metrics.compute_metrics(y_val, proba_val, threshold)

    name = model_name(algorithm, class_weight)
    number = artifacts.next_version_number(name, artifacts_root)
    version = f"{name}-v{number}"
    created = datetime.now(UTC)
    metadata = {
        "model_name": name,
        "model_version": version,
        "artifact_path": f"{name}/v{number}",
        "algorithm": algorithm,
        "class_weight": class_weight,
        "status": "experimental",
        "created_at": created.isoformat(),
        "experiment_id": f"EXP-{created.strftime('%Y%m%dT%H%M%SZ')}-{version}",
        "dataset_version": manifest["dataset_version"],
        "feature_version": manifest["feature_version"],
        "target": config.TARGET,
        "raw_features": config.RAW_FEATURES,
        "features": config.FEATURE_COLUMNS,
        "parameters": _parameters(pipeline),
        "random_seed": config.RANDOM_SEED,
        "threshold": threshold,
        "threshold_selection": "maximises F1 on the validation split",
        "split": {
            "method": manifest["split_method"],
            "cutoffs": manifest["cutoffs"],
            "train": manifest["splits"]["train"],
            "validation": manifest["splits"]["validation"],
            "test": manifest["splits"]["test"],
        },
        "metrics": {"validation": val_metrics},
        "libraries": artifacts.library_versions(),
    }
    artifacts.save_artifact(artifacts.artifact_dir(name, number, artifacts_root), pipeline, metadata)
    return metadata


def _parameters(pipeline: Pipeline) -> dict[str, Any]:
    params = pipeline[-1].get_params()
    return {k: v for k, v in params.items() if isinstance(v, (int, float, str, bool, type(None)))}


def run(
    algorithms: tuple[str, ...] = ALGORITHMS,
    class_weights: tuple[str, ...] = CLASS_WEIGHTS,
    processed_dir: Path | None = None,
    artifacts_root: Path | None = None,
) -> list[dict[str, Any]]:
    data = ds.load_dataset(processed_dir)
    manifest = ds.load_manifest(processed_dir)
    return [
        train_one(a, w, data, manifest, artifacts_root)
        for a in algorithms
        for w in class_weights
    ]

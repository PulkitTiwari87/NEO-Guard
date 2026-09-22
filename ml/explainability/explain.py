"""SHAP explanations for the pipelines produced by ml.training.

SHAP values describe how the *model* uses its inputs; they are not causal statements about
asteroids. Units differ by model: log-odds for logistic regression and XGBoost, probability for
random forest (``output_space`` says which). Contributions add up to ``prediction - base_value``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml import artifacts, config
from ml.features.engineering import build_features
from ml.preprocessing import dataset as ds
from ml.training.train import split_xy

GLOBAL_SAMPLE = 2000


def output_space(model: Any) -> str:
    return "probability" if isinstance(model, RandomForestClassifier) else "log_odds"


def _positive_class(values: Any) -> np.ndarray:
    """Normalise shap's output (list per class, 3-D array, or 2-D array) to (n, features)."""
    if isinstance(values, list):
        return np.asarray(values[1])
    values = np.asarray(values)
    return values[:, :, 1] if values.ndim == 3 else values


def _base_value(expected: Any) -> float:
    return float(np.ravel(expected)[-1])  # last entry = positive class for per-class outputs


class Explainer:
    """Wraps a fitted pipeline (features -> [scaler] -> model) with the matching SHAP explainer."""

    def __init__(self, pipeline: Pipeline, background_mean: list[float] | None = None) -> None:
        self.pre, self.model = pipeline[:-1], pipeline[-1]
        if isinstance(self.model, LogisticRegression):
            if background_mean is None:
                raise ValueError("logistic regression needs the training feature mean as background")
            mean = np.asarray(background_mean, dtype=float)
            # Independent features around the training mean (interventional SHAP for linear models).
            self._explainer = shap.LinearExplainer(self.model, (mean, np.eye(len(mean))))
        else:
            self._explainer = shap.TreeExplainer(self.model)

    def shap_values(self, transformed: Any) -> np.ndarray:
        return _positive_class(self._explainer.shap_values(np.asarray(transformed)))

    @property
    def base_value(self) -> float:
        return _base_value(self._explainer.expected_value)

    def explain(self, raw: pd.DataFrame) -> dict[str, Any]:
        """Local explanation for a single-row raw-feature frame."""
        transformed = self.pre.transform(raw)
        contributions = self.shap_values(transformed)[0]
        engineered = build_features(raw).iloc[0]
        items = [
            {"feature": name, "value": float(engineered[name]), "shap_value": float(value)}
            for name, value in zip(config.FEATURE_COLUMNS, contributions, strict=True)
        ]
        items.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
        return {"method": "SHAP", "output_space": output_space(self.model),
                "base_value": self.base_value, "contributions": items}


def global_importance(explainer: Explainer, raw: pd.DataFrame) -> list[dict[str, Any]]:
    values = explainer.shap_values(explainer.pre.transform(raw))
    mean_abs = np.abs(values).mean(axis=0)
    order = np.argsort(mean_abs)[::-1]
    return [{"feature": config.FEATURE_COLUMNS[i], "mean_abs_shap": float(mean_abs[i])}
            for i in order]


def build_global(directory: Path, data: pd.DataFrame, manifest: dict[str, Any]) -> dict[str, Any]:
    metadata = artifacts.load_metadata(directory)
    if metadata["dataset_version"] != manifest["dataset_version"]:
        raise ValueError(f"{metadata['model_version']}: dataset version mismatch; retrain")
    pipeline = artifacts.load_pipeline(directory)
    X_train, _ = split_xy(data, "train")
    background_mean = pipeline[:-1].transform(X_train).mean(axis=0)
    explainer = Explainer(pipeline, list(np.asarray(background_mean)))
    X_val, _ = split_xy(data, "validation")  # never the test split
    sample = X_val.sample(min(GLOBAL_SAMPLE, len(X_val)), random_state=config.RANDOM_SEED)
    result = {
        "model_version": metadata["model_version"],
        "split": "validation",
        "n_rows": int(len(sample)),
        "output_space": output_space(explainer.model),
        "background_mean": [float(x) for x in np.asarray(background_mean)],
        "importance": global_importance(explainer, sample),
        "caveat": "Model-behaviour attribution, not causal evidence about asteroids.",
    }
    (directory / artifacts.SHAP_FILE).write_text(
        artifacts.dumps_strict(result, indent=2), encoding="utf-8")
    return result


def run(
    model_versions: list[str] | None = None,
    processed_dir: Path | None = None,
    artifacts_root: Path | None = None,
) -> list[dict[str, Any]]:
    data = ds.load_dataset(processed_dir)
    manifest = ds.load_manifest(processed_dir)
    return [
        build_global(directory, data, manifest)
        for directory, metadata in artifacts.list_artifacts(artifacts_root)
        if not model_versions or metadata["model_version"] in model_versions
    ]

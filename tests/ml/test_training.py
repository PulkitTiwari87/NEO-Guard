"""Training protocol: fit on train only, tune on validation, reproducible, valid outputs."""
from __future__ import annotations

import json

import numpy as np
import pytest

from ml import artifacts, config
from ml.evaluation import metrics
from ml.features.engineering import build_features
from ml.preprocessing import dataset as ds
from ml.training import train

EXPECTED = {"logistic_regression", "logistic_regression_balanced", "random_forest",
            "random_forest_balanced", "xgboost", "xgboost_balanced"}


@pytest.fixture(scope="module")
def data(workspace):
    return ds.load_dataset(workspace["processed_dir"]), ds.load_manifest(workspace["processed_dir"])


def artifact_items(workspace):
    return artifacts.list_artifacts(workspace["artifacts_dir"])


def test_six_versioned_artifacts_exist(workspace):
    items = artifact_items(workspace)
    assert {md["model_name"] for _, md in items} == EXPECTED
    for directory, md in items:
        assert md["model_version"] == f"{md['model_name']}-v1" and md["status"] == "experimental"
        assert (directory / artifacts.MODEL_FILE).exists()


def test_predictions_are_valid_probabilities(workspace, data):
    frame, _ = data
    X, _ = train.split_xy(frame, "validation")
    for directory, _ in artifact_items(workspace):
        proba = artifacts.load_pipeline(directory).predict_proba(X)[:, 1]
        assert proba.shape == (len(X),) and np.isfinite(proba).all()
        assert ((proba >= 0) & (proba <= 1)).all()


@pytest.mark.parametrize("algorithm", ["random_forest", "xgboost"])
def test_training_is_reproducible_with_fixed_seed(workspace, data, tmp_path, algorithm):
    frame, manifest = data
    md = train.train_one(algorithm, "none", frame, manifest, tmp_path)
    X, _ = train.split_xy(frame, "validation")
    fresh = artifacts.load_pipeline(tmp_path / md["artifact_path"]).predict_proba(X)
    original = artifacts.load_pipeline(workspace["artifacts_dir"] / algorithm / "v1").predict_proba(X)
    # Same seed => same trees. A parallel forest averages trees in a thread-dependent order, so
    # probabilities can differ by ~1 ulp (3e-16); anything larger would be a real reproducibility bug.
    np.testing.assert_allclose(fresh, original, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(fresh[:, 1] >= 0.5, original[:, 1] >= 0.5)


def test_scaler_is_fitted_on_the_training_split_only(workspace, data):
    frame, _ = data
    pipeline = artifacts.load_pipeline(workspace["artifacts_dir"] / "logistic_regression" / "v1")
    X_train, _ = train.split_xy(frame, "train")
    np.testing.assert_allclose(pipeline["scale"].mean_, build_features(X_train).mean().to_numpy())
    all_mean = build_features(frame[config.RAW_FEATURES]).mean().to_numpy()
    assert not np.allclose(pipeline["scale"].mean_, all_mean, rtol=1e-12, atol=0)


def test_threshold_is_tuned_on_validation_only(workspace, data):
    frame, _ = data
    X_val, y_val = train.split_xy(frame, "validation")
    for directory, md in artifact_items(workspace):
        proba = artifacts.load_pipeline(directory).predict_proba(X_val)[:, 1]
        assert md["threshold"] == pytest.approx(metrics.best_f1_threshold(y_val, proba))
        assert md["metrics"]["validation"]["threshold"] == md["threshold"]


def test_metadata_is_complete_and_strict_json(workspace):
    required = {"model_name", "model_version", "artifact_path", "algorithm", "class_weight", "status",
                "created_at", "experiment_id", "dataset_version", "feature_version", "target",
                "raw_features", "features", "parameters", "random_seed", "threshold", "split",
                "metrics", "libraries"}
    for directory, md in artifact_items(workspace):
        assert required <= set(md)
        text = (directory / artifacts.METADATA_FILE).read_text(encoding="utf-8")
        json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        assert md["random_seed"] == config.RANDOM_SEED


def test_training_never_touches_the_test_split(data, tmp_path):
    frame, manifest = data
    md = train.train_one("logistic_regression", "none", frame, manifest, tmp_path)
    assert set(md["metrics"]) == {"validation"}


def test_class_weighting_is_applied_only_where_requested(workspace):
    def params(name):
        return artifacts.load_metadata(workspace["artifacts_dir"] / name / "v1")["parameters"]

    assert params("xgboost")["scale_pos_weight"] == 1.0 and params("xgboost_balanced")["scale_pos_weight"] > 1.0
    assert params("logistic_regression")["class_weight"] is None
    assert params("logistic_regression_balanced")["class_weight"] == "balanced"
    assert params("random_forest_balanced")["class_weight"] == "balanced"


def test_unknown_algorithm_is_rejected():
    with pytest.raises(ValueError, match="unknown algorithm"):
        train.make_pipeline("svm", "none", np.array([0, 1]))

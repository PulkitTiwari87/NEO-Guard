"""Metrics (hand-computed expectations) and artifact storage. Uses SYNTHETIC / TEST DATA."""
from __future__ import annotations

import json

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

from ml import artifacts
from ml.evaluation import metrics

Y = np.array([0, 0, 1, 1])
P = np.array([0.1, 0.4, 0.35, 0.8])


def test_metrics_match_hand_computed_values():
    m = metrics.compute_metrics(Y, P, threshold=0.5)  # predictions: 0,0,0,1
    assert m["confusion_matrix"] == {"tn": 2, "fp": 0, "fn": 1, "tp": 1}
    assert m["accuracy"] == pytest.approx(0.75) and m["precision"] == pytest.approx(1.0)
    assert m["recall"] == pytest.approx(0.5) and m["f1"] == pytest.approx(2 / 3)
    assert m["roc_auc"] == pytest.approx(0.75) and m["pr_auc"] == pytest.approx(5 / 6)
    assert m["prevalence"] == pytest.approx(0.5) and m["n_positive"] == 2


def test_auc_is_reported_as_undefined_with_one_class_not_invented():
    m = metrics.compute_metrics(np.zeros(4, dtype=int), P, 0.5)
    assert m["roc_auc"] is None and m["pr_auc"] is None and "undefined" in m["note"]


def test_best_f1_threshold_and_guard():
    assert metrics.best_f1_threshold(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9])) == 0.8
    with pytest.raises(ValueError, match="no positive"):
        metrics.best_f1_threshold(np.zeros(4, dtype=int), P)


def test_curves_are_bounded_and_span_the_range():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 2000)
    c = metrics.curves(y, rng.random(2000), max_points=50)
    assert len(c["roc"]["fpr"]) <= 50 and len(c["pr"]["recall"]) <= 50
    assert c["roc"]["fpr"][0] == 0.0 and c["roc"]["tpr"][-1] == 1.0


def test_bootstrap_ci_is_deterministic_and_brackets_the_estimate():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 600)
    p = y * 0.4 + rng.random(600) * 0.6
    first, second = metrics.bootstrap_ci(y, p, n_resamples=200), metrics.bootstrap_ci(y, p, n_resamples=200)
    assert first == second
    auc = metrics.compute_metrics(y, p, 0.5)["roc_auc"]
    assert first["roc_auc"][0] <= auc <= first["roc_auc"][1]


def test_json_safe_replaces_non_finite_floats_and_output_is_strict_json():
    value = {"missing": float("nan"), "big": float("inf"), "ok": [1.5, {"x": float("-inf")}]}
    safe = artifacts.json_safe(value)
    assert safe == {"missing": "nan", "big": "inf", "ok": [1.5, {"x": "-inf"}]}
    text = artifacts.dumps_strict(value)
    json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    assert artifacts.dumps_strict({"a": 1}) == '{"a": 1}'


def toy_pipeline():
    return LogisticRegression().fit(np.array([[0.0], [1.0], [2.0], [3.0]]), [0, 0, 1, 1])


def test_artifacts_are_versioned_immutable_and_discoverable(tmp_path):
    assert artifacts.next_version_number("m", tmp_path) == 1
    d1 = artifacts.artifact_dir("m", 1, tmp_path)
    artifacts.save_artifact(d1, toy_pipeline(), {"model_version": "m-v1", "x": float("nan")})
    assert artifacts.next_version_number("m", tmp_path) == 2
    with pytest.raises(FileExistsError):
        artifacts.save_artifact(d1, toy_pipeline(), {"model_version": "m-v1"})  # versions never overwritten
    artifacts.save_artifact(artifacts.artifact_dir("m", 2, tmp_path), toy_pipeline(), {"model_version": "m-v2"})
    assert [md["model_version"] for _, md in artifacts.list_artifacts(tmp_path)] == ["m-v1", "m-v2"]
    directory, md = artifacts.find_artifact("m-v1", tmp_path)
    assert md["x"] == "nan" and artifacts.load_pipeline(directory).predict([[3.0]])[0] == 1
    with pytest.raises(FileNotFoundError):
        artifacts.find_artifact("nope-v9", tmp_path)

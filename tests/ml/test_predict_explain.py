"""Inference contract and SHAP correctness. Uses SYNTHETIC / TEST DATA."""
from __future__ import annotations

import json
import shutil

import numpy as np
import pytest

from ml import artifacts, config
from ml.inference.predict import IncompatibleArtifact, load_model, predict
from ml.preprocessing import dataset as ds
from ml.training import train

FEATURES = {
    "semi_major_axis_au": 1.2, "eccentricity": 0.5, "inclination_deg": 10.0,
    "perihelion_distance_au": 0.6, "aphelion_distance_au": 1.8,
    "ascending_node_deg": 100.0, "argument_of_perihelion_deg": 50.0,
}


def artifact_items(workspace):
    return artifacts.list_artifacts(workspace["artifacts_dir"])


def test_prediction_contract_for_every_model(workspace):
    for directory, md in artifact_items(workspace):
        result = predict(load_model(directory), FEATURES)
        assert set(result) == {"prediction", "probability", "threshold", "model_version", "explanation"}
        assert result["model_version"] == md["model_version"]
        assert 0.0 <= result["probability"] <= 1.0 and result["prediction"] in (0, 1)
        assert result["prediction"] == int(result["probability"] >= md["threshold"])
        assert len(result["explanation"]["contributions"]) == len(config.FEATURE_COLUMNS)


def test_shap_values_add_up_to_the_model_output(workspace):
    for directory, _ in artifact_items(workspace):
        result = predict(load_model(directory), FEATURES)
        e = result["explanation"]
        total = e["base_value"] + sum(c["shap_value"] for c in e["contributions"])
        reconstructed = total if e["output_space"] == "probability" else 1 / (1 + np.exp(-total))
        assert reconstructed == pytest.approx(result["probability"], abs=1e-5)


def test_explanation_names_all_features_sorted_by_impact(workspace):
    directory, _ = artifact_items(workspace)[0]
    e = predict(load_model(directory), FEATURES)["explanation"]
    assert e["method"] == "SHAP" and e["output_space"] in {"log_odds", "probability"}
    assert {c["feature"] for c in e["contributions"]} == set(config.FEATURE_COLUMNS)
    impacts = [abs(c["shap_value"]) for c in e["contributions"]]
    assert impacts == sorted(impacts, reverse=True)


def test_explanation_is_optional(workspace):
    directory, _ = artifact_items(workspace)[0]
    assert predict(load_model(directory), FEATURES, explain=False)["explanation"] is None


def test_missing_feature_is_an_error(workspace):
    directory, _ = artifact_items(workspace)[0]
    with pytest.raises(ValueError, match="missing features"):
        predict(load_model(directory), {k: v for k, v in FEATURES.items() if k != "eccentricity"})


def test_artifact_with_a_different_feature_version_is_refused(workspace, tmp_path):
    source, md = artifact_items(workspace)[0]
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)
    artifacts.write_metadata(copy, {**md, "feature_version": "features-v0"})
    with pytest.raises(IncompatibleArtifact):
        load_model(copy)


def test_linear_model_without_shap_background_returns_no_explanation(workspace, tmp_path):
    source, _ = next(i for i in artifact_items(workspace) if i[1]["model_name"] == "logistic_regression")
    copy = tmp_path / "lr"
    shutil.copytree(source, copy)
    (copy / artifacts.SHAP_FILE).unlink()
    result = predict(load_model(copy), FEATURES)
    assert result["explanation"] is None and 0 <= result["probability"] <= 1


def test_global_importance_is_ordered_finite_and_uses_validation_data(workspace):
    for directory, md in artifact_items(workspace):
        g = json.loads((directory / artifacts.SHAP_FILE).read_text())
        values = [i["mean_abs_shap"] for i in g["importance"]]
        assert g["split"] == "validation" and g["model_version"] == md["model_version"]
        assert values == sorted(values, reverse=True) and np.isfinite(values).all()
        assert {i["feature"] for i in g["importance"]} == set(config.FEATURE_COLUMNS)
        assert "not causal" in g["caveat"].lower()


def test_serving_path_equals_training_path(workspace):
    """Same preprocessing at train and predict time: pipeline output == manual two-step path."""
    frame = ds.load_dataset(workspace["processed_dir"])
    X, _ = train.split_xy(frame, "test")
    for directory, _ in artifact_items(workspace):
        pipeline = artifacts.load_pipeline(directory)
        manual = pipeline[-1].predict_proba(pipeline[:-1].transform(X))[:, 1]
        np.testing.assert_allclose(pipeline.predict_proba(X)[:, 1], manual)
        row = predict(load_model(directory), {c: float(X.iloc[0][c]) for c in config.RAW_FEATURES},
                      explain=False)
        assert row["probability"] == pytest.approx(manual[0])

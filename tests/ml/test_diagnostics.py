"""ml/diagnostics smoke tests. Uses the SYNTHETIC / TEST DATA `workspace` fixture (see
tests/helpers.py); never touches data/ or ml/artifacts/.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml import artifacts, config
from ml.diagnostics import (
    _common,
    calibration,
    case_study,
    definition_reconstruction,
    distribution_shift,
    subgroup,
)
from ml.inference import predict as inference


def test_orbit_class_names_map_documented_cneos_codes():
    assert _common.orbit_class_name("IEO") == "Atira"
    assert _common.orbit_class_name("ATE") == "Aten"
    assert _common.orbit_class_name("APO") == "Apollo"
    assert _common.orbit_class_name("AMO") == "Amor"
    assert _common.orbit_class_name("XYZ") == "XYZ"  # unknown code passes through, not invented


def test_diagnostic_artifact_root_never_overlaps_production_registry():
    diag_root = str(_common.ARTIFACTS_DIR.resolve())
    prod_root = str(config.ARTIFACTS_DIR.resolve())
    assert diag_root != prod_root
    assert not diag_root.startswith(prod_root)
    assert not prod_root.startswith(diag_root)


def test_subgroup_below_min_positives_reports_insufficient_sample():
    y = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0])  # 1 positive, below MIN_POSITIVES; SYNTHETIC / TEST DATA
    proba = np.linspace(0.1, 0.9, len(y))
    result = subgroup._evaluate_subgroup(y, proba, threshold=0.5)
    assert result["metrics"] == _common.INSUFFICIENT_SAMPLE
    assert result["support"] == len(y) and result["positives"] == 1


def test_subgroup_at_or_above_min_positives_reports_real_metrics():
    rng = np.random.default_rng(0)
    y = np.array([1] * _common.MIN_POSITIVES + [0] * 40)  # SYNTHETIC / TEST DATA
    proba = rng.uniform(0, 1, size=len(y))
    result = subgroup._evaluate_subgroup(y, proba, threshold=0.5)
    assert result["metrics"] != _common.INSUFFICIENT_SAMPLE
    assert 0 <= result["metrics"]["pr_auc"] <= 1


def test_with_interim_columns_raise_vs_drop(workspace):
    data = pd.read_csv(workspace["processed_dir"] / "neo_ml_dataset.csv", dtype={"designation": str})
    joined, n_bad = _common.with_interim_columns(
        data, workspace["interim_dir"], columns=("orbit_class",), on_missing="raise")
    assert n_bad == 0 and "orbit_class" in joined.columns and len(joined) == len(data)


def test_distribution_shift_runs_on_synthetic_workspace_and_writes_report(workspace, tmp_path):
    out = tmp_path / "distribution_shift.json"
    report = distribution_shift.run(
        processed_dir=workspace["processed_dir"], interim_dir=workspace["interim_dir"], output_file=out)
    assert out.exists()
    assert report["dataset_version"] == workspace["manifest"]["dataset_version"]
    assert set(report["orbit_class_composition"]) == {"train", "validation", "test"}
    assert len(report["feature_distribution_shift_train_vs_test"]) == len(config.RAW_FEATURES)
    assert "inconclusive" in report["interpretation"]


def test_subgroup_runs_on_synthetic_workspace(workspace, tmp_path):
    out = tmp_path / "subgroup.json"
    report = subgroup.run(
        model_version="random_forest-v1", processed_dir=workspace["processed_dir"],
        interim_dir=workspace["interim_dir"], artifacts_root=workspace["artifacts_dir"],
        output_file=out)
    assert out.exists()
    assert report["model_version"] == "random_forest-v1"
    for split in ("validation", "test"):
        assert "overall" in report["splits"][split]
        assert "by_orbit_class" in report["splits"][split]


def test_calibration_runs_on_synthetic_workspace_and_never_touches_the_model(workspace, tmp_path):
    out = tmp_path / "calibration.json"
    report = calibration.run(
        model_version="random_forest-v1", processed_dir=workspace["processed_dir"],
        artifacts_root=workspace["artifacts_dir"], output_file=out)
    assert out.exists()
    assert report["split_evaluated"] == "validation"
    assert report["calibration_transform_applied_to_production_model"] is False
    assert 0 <= report["brier_score"]


def test_case_study_predicts_a_real_row_from_the_workspace(workspace, tmp_path, monkeypatch):
    interim = pd.read_csv(workspace["interim_dir"] / "neo_objects.csv", dtype={"designation": str})
    spkid = int(interim.iloc[0]["spkid"])
    out = tmp_path / "case_study.json"

    monkeypatch.setattr(case_study, "APOPHIS_SPKID", spkid)  # a row that exists in the synthetic fixture
    report = case_study.run(
        model_version="random_forest-v1", interim_dir=workspace["interim_dir"],
        artifacts_root=workspace["artifacts_dir"], output_file=out)
    assert out.exists()
    assert report["spkid"] == spkid
    assert report["model_decision"] in ("potentially_hazardous", "not_potentially_hazardous")


def test_definition_reconstruction_beats_the_orbital_only_baseline(workspace, tmp_path):
    """The whole point of this diagnostic: giving the model H/MOID must make it near-trivial."""
    artifacts_root = tmp_path / "diagnostic_artifacts"
    out = tmp_path / "definition_reconstruction.json"
    report = definition_reconstruction.run(
        processed_dir=workspace["processed_dir"], interim_dir=workspace["interim_dir"],
        artifacts_root=artifacts_root, output_file=out)
    assert out.exists()
    assert report["artifact_root_isolated_from_production"] is True
    rf_test_pr_auc = report["algorithms"]["random_forest"]["metrics"]["test"]["pr_auc"]
    assert rf_test_pr_auc is not None and rf_test_pr_auc > 0.9  # near-perfect once H/MOID are inputs
    # never registered where `python -m app.cli sync-models` (ml.artifacts.list_artifacts) would find it
    found_versions = {md["model_version"] for _, md in artifacts.list_artifacts(workspace["artifacts_dir"])}
    assert not any("defn-recon" in v for v in found_versions)


def test_definition_reconstruction_feature_version_is_refused_by_the_real_inference_loader(tmp_path):
    assert definition_reconstruction.FEATURE_VERSION != config.FEATURE_VERSION
    directory = tmp_path / "logistic_regression" / "v1"
    directory.mkdir(parents=True)
    artifacts.write_metadata(directory, {
        "model_version": "logistic_regression-diagnostic-defn-recon-v1",
        "feature_version": definition_reconstruction.FEATURE_VERSION,
        "raw_features": list(config.RAW_FEATURES) + list(definition_reconstruction.EXTRA_RAW_FEATURES),
    })
    with pytest.raises(inference.IncompatibleArtifact):
        inference.load_model(directory)

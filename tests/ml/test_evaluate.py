"""Held-out evaluation and experiment logging. Uses SYNTHETIC / TEST DATA (never the real log)."""
from __future__ import annotations

import json
import shutil

import pytest

from ml import artifacts
from ml.evaluation import evaluate
from ml.preprocessing import dataset as ds


def items(workspace):
    return artifacts.list_artifacts(workspace["artifacts_dir"])


def test_test_metrics_and_curves_are_stored_for_every_model(workspace):
    n_test = workspace["manifest"]["splits"]["test"]["rows"]
    for directory, md in items(workspace):
        test = md["metrics"]["test"]
        assert test["n"] == n_test and 0 <= test["roc_auc"] <= 1 and 0 <= test["pr_auc"] <= 1
        assert test["threshold"] == md["threshold"]  # threshold comes from validation, not test
        assert test["bootstrap_ci"]["roc_auc"][0] <= test["roc_auc"] <= test["bootstrap_ci"]["roc_auc"][1]
        ev = json.loads((directory / artifacts.EVALUATION_FILE).read_text())
        assert ev["split"] == "test" and ev["curves"]["roc"]["fpr"][0] == 0.0
        assert ev["dataset_version"] == md["dataset_version"]


def test_experiment_log_has_one_entry_per_model_and_is_idempotent(workspace, tmp_path):
    log = workspace["log_doc"]
    text = log.read_text(encoding="utf-8")
    assert text.count("### EXP-") == 6 and "SYNTHETIC" in text
    copy = tmp_path / "EXPERIMENTS.md"
    shutil.copy(log, copy)
    evaluate.run(processed_dir=workspace["processed_dir"], artifacts_root=workspace["artifacts_dir"],
                 log_doc=copy)
    assert copy.read_text(encoding="utf-8").count("### EXP-") == 6  # no duplicates on re-run


def test_logged_entry_contains_the_real_computed_values(workspace):
    _, md = items(workspace)[0]
    entry = evaluate.markdown_entry(md)
    assert md["experiment_id"] in entry and md["dataset_version"] in entry
    assert f"{md['metrics']['test']['pr_auc']:.4f}" in entry
    assert f"{md['metrics']['validation']['roc_auc']:.4f}" in entry
    assert str(md["split"]["test"]["rows"]) in entry


def test_evaluation_refuses_a_model_trained_on_another_dataset(workspace, tmp_path):
    source, md = items(workspace)[0]
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)
    artifacts.write_metadata(copy, {**md, "dataset_version": "some-other-dataset"})
    data = ds.load_dataset(workspace["processed_dir"])
    with pytest.raises(ValueError, match="retrain before evaluating"):
        evaluate.evaluate_artifact(copy, data, workspace["manifest"])

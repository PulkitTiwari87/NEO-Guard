"""Evaluate trained artifacts on the held-out test split and log the experiment.

Model selection is done on validation metrics *before* this step. Test metrics are reported
for every candidate; they must not be used to tune anything (docs/ML_WORKFLOW.md).
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ml import artifacts, config
from ml.evaluation import metrics
from ml.preprocessing import dataset as ds
from ml.training.train import split_xy

SEPARATOR = "<!-- experiment-log-entries -->"


def evaluate_artifact(directory: Path, data: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    metadata = artifacts.load_metadata(directory)
    for key in ("dataset_version", "feature_version"):
        if metadata[key] != manifest[key]:
            raise ValueError(
                f"{metadata['model_version']}: trained on {key}={metadata[key]!r} but the "
                f"processed dataset is {manifest[key]!r}; retrain before evaluating"
            )
    pipeline = artifacts.load_pipeline(directory)
    X_test, y_test = split_xy(data, "test")
    proba = pipeline.predict_proba(X_test)[:, 1]

    test_metrics = metrics.compute_metrics(y_test, proba, metadata["threshold"])
    interval = metrics.bootstrap_ci(y_test, proba)
    evaluation = {
        "model_version": metadata["model_version"],
        "split": "test",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "dataset_version": metadata["dataset_version"],
        "metrics": test_metrics,
        "bootstrap_ci": interval,
        "curves": metrics.curves(y_test, proba),
    }
    (directory / artifacts.EVALUATION_FILE).write_text(
        artifacts.dumps_strict(evaluation), encoding="utf-8")
    metadata["metrics"]["test"] = {**test_metrics, "bootstrap_ci": interval}
    artifacts.write_metadata(directory, metadata)
    return metadata


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def markdown_entry(metadata: dict[str, Any]) -> str:
    val, test = metadata["metrics"]["validation"], metadata["metrics"]["test"]
    ci, split = test["bootstrap_ci"], metadata["split"]
    params = {k: v for k, v in metadata["parameters"].items() if v is not None}
    cm = test["confusion_matrix"]

    def describe(name: str) -> str:
        s = split[name]
        return (f"{s['rows']} rows, {s['positives']} positives ({s['positive_rate']:.2%}), "
                f"first_obs_year {s['first_obs_year_min']}-{s['first_obs_year_max']}")

    rows = [(label, val.get(key), test.get(key)) for label, key in [
        ("Accuracy", "accuracy"), ("Precision", "precision"), ("Recall", "recall"),
        ("F1", "f1"), ("ROC-AUC", "roc_auc"), ("PR-AUC", "pr_auc")]]
    table = "\n".join(f"| {label} | {_fmt(v)} | {_fmt(t)} |" for label, v, t in rows)
    ci_line = (f"Test 95% bootstrap CI ({ci['n_resamples']} resamples): "
               f"ROC-AUC [{ci['roc_auc'][0]:.4f}, {ci['roc_auc'][1]:.4f}], "
               f"PR-AUC [{ci['pr_auc'][0]:.4f}, {ci['pr_auc'][1]:.4f}]")
    return f"""
### {metadata['experiment_id']}

```
Experiment ID: {metadata['experiment_id']}
Date: {metadata['created_at']}
Dataset version: {metadata['dataset_version']}
Feature version: {metadata['feature_version']}
Model: {metadata['model_version']} ({metadata['algorithm']}, class_weight={metadata['class_weight']})
Parameters: {json.dumps(params, sort_keys=True)}
Random seed: {metadata['random_seed']}
Training split: {describe('train')}
Validation split: {describe('validation')}
Test split: {describe('test')}
Decision threshold: {metadata['threshold']:.4f} ({metadata['threshold_selection']})
Status: {metadata['status']}
```

| Metric | Validation | Test |
|--------|-----------:|-----:|
{table}

- No-skill PR-AUC (prevalence): validation {val['prevalence']:.4f}, test {test['prevalence']:.4f}
- {ci_line}
- Test confusion matrix: TN={cm['tn']} FP={cm['fp']} FN={cm['fn']} TP={cm['tp']}
"""


def append_experiment(metadata: dict[str, Any], doc: Path | None = None) -> bool:
    """Append the entry to docs/EXPERIMENTS.md unless that experiment is already logged."""
    doc = doc or config.EXPERIMENTS_DOC
    text = doc.read_text(encoding="utf-8")
    if f"### {metadata['experiment_id']}" in text:
        return False
    if SEPARATOR not in text:
        text = text.rstrip() + f"\n\n{SEPARATOR}\n"
    doc.write_text(text.rstrip() + "\n" + markdown_entry(metadata), encoding="utf-8")
    return True


def run(
    model_versions: list[str] | None = None,
    processed_dir: Path | None = None,
    artifacts_root: Path | None = None,
    log_doc: Path | None = None,
) -> list[dict[str, Any]]:
    data = ds.load_dataset(processed_dir)
    manifest = ds.load_manifest(processed_dir)
    results = []
    for directory, metadata in artifacts.list_artifacts(artifacts_root):
        if model_versions and metadata["model_version"] not in model_versions:
            continue
        updated = evaluate_artifact(directory, data, manifest)
        append_experiment(updated, log_doc)
        results.append(updated)
    return results

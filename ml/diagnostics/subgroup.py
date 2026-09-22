"""Subgroup (orbital-class) evaluation of the default production model.

Diagnostic only. Loads an existing artifact from ml/artifacts/ (the real production registry)
read-only and scores it; never retrains or modifies the model. See docs/EXPERIMENTS.md
"Experiment 2: Subgroup/orbital-class evaluation".
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from ml import artifacts, config
from ml.diagnostics import _common
from ml.evaluation import metrics
from ml.preprocessing import dataset as ds

OUTPUT_FILE = _common.OUTPUT_DIR / "subgroup_evaluation.json"
DEFAULT_MODEL_VERSION = "random_forest-v1"


def _evaluate_subgroup(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict[str, Any]:
    n = int(len(y_true))
    n_pos = int(y_true.sum()) if n else 0
    result: dict[str, Any] = {"support": n, "positives": n_pos, "prevalence": (n_pos / n) if n else None}
    if n == 0 or n_pos < _common.MIN_POSITIVES or n_pos == n:
        result["metrics"] = _common.INSUFFICIENT_SAMPLE
        return result
    m = metrics.compute_metrics(y_true, proba, threshold)
    result["metrics"] = {**m, "bootstrap_ci": metrics.bootstrap_ci(y_true, proba)}
    return result


def run(
    model_version: str = DEFAULT_MODEL_VERSION,
    processed_dir: Path | None = None,
    interim_dir: Path | None = None,
    artifacts_root: Path | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    directory, metadata = artifacts.find_artifact(model_version, artifacts_root)
    pipeline = artifacts.load_pipeline(directory)
    threshold = float(metadata["threshold"])

    data = ds.load_dataset(processed_dir)
    manifest = ds.load_manifest(processed_dir)
    data, _ = _common.with_interim_columns(data, interim_dir, columns=("orbit_class",))

    report: dict[str, Any] = {
        "diagnostic": "subgroup_evaluation",
        "generated_at": datetime.now(UTC).isoformat(),
        "model_version": model_version,
        "model_status": metadata["status"],
        "dataset_version": manifest["dataset_version"],
        "feature_version": manifest["feature_version"],
        "threshold": threshold,
        "min_positives_for_full_metrics": _common.MIN_POSITIVES,
        "orbit_class_names": {c: _common.orbit_class_name(c) for c in sorted(data["orbit_class"].unique())},
        "splits": {},
        "libraries": artifacts.library_versions(),
    }

    for split in ("validation", "test"):
        part = data[data["split"] == split]
        X = part[config.RAW_FEATURES]
        y = part[config.TARGET].to_numpy()
        proba = pipeline.predict_proba(X)[:, 1]
        codes = part["orbit_class"].to_numpy()

        by_class: dict[str, Any] = {}
        for code in sorted(part["orbit_class"].unique()):
            mask = codes == code
            by_class[code] = {
                "orbit_class_name": _common.orbit_class_name(code),
                **_evaluate_subgroup(y[mask], proba[mask], threshold),
            }
        report["splits"][split] = {
            "overall": _evaluate_subgroup(y, proba, threshold),
            "by_orbit_class": by_class,
        }

    out = output_file or OUTPUT_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(artifacts.dumps_strict(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        run()
    except FileNotFoundError as exc:
        print(f"SUBGROUP EVALUATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"wrote {OUTPUT_FILE}")

"""Calibration diagnostic for the default production model, evaluated on the validation split.

Diagnostic only: no calibration transform is fit or applied to the served model. See
docs/EXPERIMENTS.md "Experiment 3: Calibration diagnostic".
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

from ml import artifacts
from ml.diagnostics import _common
from ml.preprocessing import dataset as ds
from ml.training.train import split_xy

OUTPUT_FILE = _common.OUTPUT_DIR / "calibration.json"
DEFAULT_MODEL_VERSION = "random_forest-v1"
N_BINS = 10

SPLIT_EVALUATED_REASON = (
    "Test is reserved for the single final evaluation per model (docs/ML_WORKFLOW.md); this "
    "diagnostic uses validation instead. Validation is already reused for threshold tuning "
    "(ml.training.train); reusing it again here for a read-only diagnostic that selects between "
    "no models and feeds back into no training adds no new leakage. No separate calibration "
    "split exists in this project (docs/DATA_LEAKAGE.md defines only train/validation/test)."
)


def run(
    model_version: str = DEFAULT_MODEL_VERSION,
    processed_dir: Path | None = None,
    artifacts_root: Path | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    directory, metadata = artifacts.find_artifact(model_version, artifacts_root)
    pipeline = artifacts.load_pipeline(directory)
    data = ds.load_dataset(processed_dir)
    manifest = ds.load_manifest(processed_dir)
    X_val, y_val = split_xy(data, "validation")
    proba = pipeline.predict_proba(X_val)[:, 1]

    brier = float(brier_score_loss(y_val, proba))
    no_skill_brier = float(brier_score_loss(y_val, np.full_like(proba, y_val.mean())))
    frac_pos, mean_pred = calibration_curve(y_val, proba, n_bins=N_BINS, strategy="quantile")

    report: dict[str, Any] = {
        "diagnostic": "calibration",
        "generated_at": datetime.now(UTC).isoformat(),
        "model_version": model_version,
        "model_status": metadata["status"],
        "dataset_version": manifest["dataset_version"],
        "split_evaluated": "validation",
        "split_evaluated_reason": SPLIT_EVALUATED_REASON,
        "n": int(len(y_val)),
        "n_positive": int(y_val.sum()),
        "brier_score": brier,
        "no_skill_brier_score": no_skill_brier,
        "reliability_curve": {
            "n_bins_requested": N_BINS,
            "strategy": "quantile",
            "n_bins_returned": int(len(frac_pos)),
            "mean_predicted_probability": [float(x) for x in mean_pred],
            "observed_frequency": [float(x) for x in frac_pos],
        },
        "calibration_transform_applied_to_production_model": False,
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
        print(f"CALIBRATION DIAGNOSTIC FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"wrote {OUTPUT_FILE}")

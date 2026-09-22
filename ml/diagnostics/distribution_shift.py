"""Distribution-shift investigation (docs/EXPERIMENTS.md "Distribution shift investigation").

Diagnostic only: reads the existing processed dataset and split manifest and adds orbit-class
composition, prevalence-by-discovery-year, and a train-vs-test statistical comparison per raw
feature. Nothing here retrains or re-splits anything; ml.training/ml.preprocessing/ml.features
(the primary experiment) are untouched.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from scipy import stats

from ml import artifacts, config
from ml.diagnostics import _common
from ml.preprocessing import dataset as ds

OUTPUT_FILE = _common.OUTPUT_DIR / "distribution_shift.json"


def _prevalence_by_year(data: pd.DataFrame) -> list[dict[str, Any]]:
    g = data.groupby("first_obs_year")[config.TARGET].agg(rows="count", positives="sum")
    g["prevalence"] = g["positives"] / g["rows"]
    return [{"first_obs_year": int(year), **row} for year, row in g.to_dict("index").items()]


def _orbit_class_composition(data: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for split in ds.SPLITS:
        part = data[data["split"] == split]
        rows = []
        for code, group in part.groupby("orbit_class"):
            rows.append({
                "orbit_class": code,
                "orbit_class_name": _common.orbit_class_name(code),
                "support": int(len(group)),
                "positives": int(group[config.TARGET].sum()),
                "prevalence": float(group[config.TARGET].mean()),
            })
        result[split] = sorted(rows, key=lambda r: -r["support"])
    return result


def _feature_distribution_shift(data: pd.DataFrame) -> list[dict[str, Any]]:
    """Two-sample Kolmogorov-Smirnov test, train vs test, per raw feature."""
    train = data[data["split"] == "train"]
    test = data[data["split"] == "test"]
    rows = []
    for col in config.RAW_FEATURES:
        d, p = stats.ks_2samp(train[col].to_numpy(), test[col].to_numpy())
        rows.append({
            "feature": col,
            "train_mean": float(train[col].mean()), "train_std": float(train[col].std()),
            "test_mean": float(test[col].mean()), "test_std": float(test[col].std()),
            "ks_statistic": float(d), "ks_pvalue": float(p),
        })
    return rows


def run(
    processed_dir: Path | None = None,
    interim_dir: Path | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    manifest = ds.load_manifest(processed_dir)
    data = ds.load_dataset(processed_dir)
    data, _ = _common.with_interim_columns(data, interim_dir, columns=("orbit_class",))

    report: dict[str, Any] = {
        "diagnostic": "distribution_shift",
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_version": manifest["dataset_version"],
        "feature_version": manifest["feature_version"],
        "split_method": manifest["split_method"],
        "splits": manifest["splits"],  # source of truth (ml.preprocessing.dataset), not recomputed
        "orbit_class_composition": _orbit_class_composition(data),
        "prevalence_by_first_obs_year": _prevalence_by_year(data),
        "feature_distribution_shift_train_vs_test": _feature_distribution_shift(data),
        "libraries": artifacts.library_versions(),
        "interpretation": {
            "established": [
                "PHA prevalence falls monotonically from train to validation to test "
                "(see 'splits' above) — this is directly measured, not inferred.",
                "Orbit-class composition and the per-feature train/test distributions differ "
                "measurably (see ks_statistic/ks_pvalue: a small p-value rejects the null "
                "hypothesis that train and test are drawn from the same distribution).",
            ],
            "inconclusive": [
                "The root cause of the prevalence shift (why recent discoveries skew toward "
                "small, non-PHA objects) cannot be established from this dataset alone: it would "
                "require survey completeness / discovery-effort data that is not part of the "
                "SBDB snapshot used here. INCONCLUSIVE.",
            ],
        },
    }
    out = output_file or OUTPUT_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(artifacts.dumps_strict(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        result = run()
    except FileNotFoundError as exc:
        print(f"DISTRIBUTION SHIFT ANALYSIS FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"wrote {OUTPUT_FILE}")

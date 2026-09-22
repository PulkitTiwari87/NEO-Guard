"""Shared helpers for ml/diagnostics.

Nothing here writes to ``ml.config.ARTIFACTS_DIR``; see ``ml/diagnostics/__init__.py``.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml import config

DIAGNOSTICS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DIAGNOSTICS_DIR / "output"
ARTIFACTS_DIR = DIAGNOSTICS_DIR / "artifacts"

# SBDB `class` values (docs/DATA_SOURCE.md CNEOS reference) -> the CNEOS orbital-group names.
# This is the classification already computed by JPL and validated into `orbit_class`
# (ml/validation/schema.py); it is not re-derived here (see docs/EXPERIMENTS.md).
ORBIT_CLASS_NAMES = {
    "IEO": "Atira",
    "ATE": "Aten",
    "APO": "Apollo",
    "AMO": "Amor",
}

INSUFFICIENT_SAMPLE = "INSUFFICIENT SAMPLE"
MIN_POSITIVES = 10  # below this, precision/recall/F1/PR-AUC/ROC-AUC are not reported for a subgroup


def orbit_class_name(code: str) -> str:
    return ORBIT_CLASS_NAMES.get(code, code)


def load_interim(interim_dir: Path | None = None) -> pd.DataFrame:
    path = (interim_dir or config.INTERIM_DIR) / "neo_objects.csv"
    return pd.read_csv(path, dtype={"designation": str}, low_memory=False)


def with_interim_columns(
    data: pd.DataFrame,
    interim_dir: Path | None,
    columns: tuple[str, ...],
    on_missing: str = "raise",
) -> tuple[pd.DataFrame, int]:
    """Join extra interim-only columns (e.g. orbit_class, H, MOID) onto a processed-ML dataset.

    Returns ``(joined_dataframe, n_rows_dropped)``. ``on_missing="raise"`` errors if any
    requested column is null after the join (used for orbit_class, never null for eligible
    rows); ``on_missing="drop"`` removes rows with a null value in any requested column (used
    for H/MOID, missing for a documented few objects; docs/DATA_SOURCE.md) and reports how many.
    """
    interim = load_interim(interim_dir)[["spkid", *columns]]
    merged = data.merge(interim, on="spkid", how="left", validate="many_to_one")
    bad = merged[list(columns)].isna().any(axis=1)
    n_bad = int(bad.sum())
    if n_bad and on_missing == "raise":
        raise ValueError(f"{n_bad} rows failed to join interim columns {columns}")
    if n_bad and on_missing == "drop":
        merged = merged[~bad].reset_index(drop=True)
    return merged, n_bad

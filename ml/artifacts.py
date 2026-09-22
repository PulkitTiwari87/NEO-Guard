"""Versioned model artifacts on disk: ``<MODEL_DIR>/<name>/v<N>/{model.joblib, metadata.json, ...}``.

This is the file-side model registry. The database ``models`` table is synced from it by
``python -m app.cli sync-models`` and is authoritative for a model's *status* afterwards.
"""
from __future__ import annotations

import json
import math
import platform
import re
from pathlib import Path
from typing import Any

import joblib

from ml import config

MODEL_FILE = "model.joblib"
METADATA_FILE = "metadata.json"
EVALUATION_FILE = "evaluation.json"
SHAP_FILE = "shap_global.json"
STATUSES = ("experimental", "validated", "production", "deprecated")


def next_version_number(name: str, root: Path | None = None) -> int:
    folder = (root or config.ARTIFACTS_DIR) / name
    numbers = [int(m.group(1)) for p in folder.glob("v*") if (m := re.fullmatch(r"v(\d+)", p.name))]
    return max(numbers, default=0) + 1


def artifact_dir(name: str, number: int, root: Path | None = None) -> Path:
    return (root or config.ARTIFACTS_DIR) / name / f"v{number}"


def library_versions() -> dict[str, str]:
    import numpy
    import pandas
    import sklearn
    import xgboost

    return {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scikit-learn": sklearn.__version__,
        "xgboost": xgboost.__version__,
    }


def save_artifact(directory: Path, pipeline: Any, metadata: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=False)  # versions are immutable
    joblib.dump(pipeline, directory / MODEL_FILE)
    write_metadata(directory, metadata)


def json_safe(value: Any) -> Any:
    """Replace non-finite floats (e.g. XGBoost's ``missing=NaN``) with strings.

    ``NaN``/``Infinity`` are not valid JSON: PostgreSQL JSONB and browsers reject them.
    """
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def dumps_strict(value: Any, **kwargs: Any) -> str:
    """Serialise to strict JSON; raises instead of emitting NaN/Infinity."""
    return json.dumps(json_safe(value), allow_nan=False, **kwargs)


def write_metadata(directory: Path, metadata: dict[str, Any]) -> None:
    (directory / METADATA_FILE).write_text(dumps_strict(metadata, indent=2), encoding="utf-8")


def load_metadata(directory: Path) -> dict[str, Any]:
    return json.loads((directory / METADATA_FILE).read_text(encoding="utf-8"))


def load_pipeline(directory: Path) -> Any:
    """Load a trained pipeline. Uses pickle: only load artifacts from a trusted MODEL_DIR."""
    return joblib.load(directory / MODEL_FILE)


def list_artifacts(root: Path | None = None) -> list[tuple[Path, dict[str, Any]]]:
    """All (directory, metadata) pairs under the artifacts root, sorted by version string."""
    root = root or config.ARTIFACTS_DIR
    found = [(p.parent, load_metadata(p.parent)) for p in root.glob(f"*/v*/{METADATA_FILE}")]
    return sorted(found, key=lambda item: item[1]["model_version"])


def find_artifact(model_version: str, root: Path | None = None) -> tuple[Path, dict[str, Any]]:
    for directory, metadata in list_artifacts(root):
        if metadata["model_version"] == model_version:
            return directory, metadata
    raise FileNotFoundError(f"No artifact with model_version={model_version!r}")

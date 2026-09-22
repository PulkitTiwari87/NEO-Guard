"""Apophis qualitative case study (docs/EXPERIMENTS.md / docs/MODEL_CARD.md).

Recomputes the current model's score for Apophis (spkid 20099942) via the real
ml.inference.predict path against the currently stored data snapshot, so the reported number is
generated, not retyped. This is a single real-world example, not a validation of overall model
performance.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ml import artifacts, config
from ml.diagnostics import _common
from ml.inference import predict as inference

OUTPUT_FILE = _common.OUTPUT_DIR / "apophis_case_study.json"
APOPHIS_SPKID = 20099942
DEFAULT_MODEL_VERSION = "random_forest-v1"
LABEL = "qualitative case study / real-world example — not a validation of overall model performance"


def run(
    model_version: str = DEFAULT_MODEL_VERSION,
    interim_dir: Path | None = None,
    artifacts_root: Path | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    interim = _common.load_interim(interim_dir)
    matches = interim[interim["spkid"] == APOPHIS_SPKID]
    if matches.empty:
        raise ValueError(
            f"spkid {APOPHIS_SPKID} (Apophis) not found in "
            f"{(interim_dir or config.INTERIM_DIR) / 'neo_objects.csv'}")
    row = matches.iloc[0]

    directory, metadata = artifacts.find_artifact(model_version, artifacts_root)
    model = inference.load_model(directory)
    features = {c: float(row[c]) for c in config.RAW_FEATURES}
    result = inference.predict(model, features, explain=False)

    report: dict[str, Any] = {
        "diagnostic": "apophis_case_study",
        "label": LABEL,
        "generated_at": datetime.now(UTC).isoformat(),
        "designation": str(row["designation"]),
        "full_name": str(row["full_name"]),
        "spkid": int(row["spkid"]),
        "jpl_pha_status": bool(row["is_potentially_hazardous"]),
        "orbit_class": str(row["orbit_class"]),
        "orbit_class_name": _common.orbit_class_name(str(row["orbit_class"])),
        "absolute_magnitude_h": float(row["absolute_magnitude_h"]),
        "earth_moid_au": float(row["earth_moid_au"]),
        "model_version": model_version,
        "model_status": metadata["status"],
        "model_score": result["probability"],
        "decision_threshold": result["threshold"],
        "model_decision": "potentially_hazardous" if result["prediction"] else "not_potentially_hazardous",
        "libraries": artifacts.library_versions(),
    }
    out = output_file or OUTPUT_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(artifacts.dumps_strict(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        r = run()
    except (FileNotFoundError, ValueError) as exc:
        print(f"APOPHIS CASE STUDY FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"wrote {OUTPUT_FILE}: score={r['model_score']:.4f} decision={r['model_decision']}")

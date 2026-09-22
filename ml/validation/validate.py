"""Validate raw snapshots and write interim (validated, normalised) datasets.

Input : data/raw/jpl_sbdb and data/raw/jpl_cad snapshots (never modified).
Output: data/interim/{neo_objects,close_approaches}.csv, rejected_*.jsonl, validation_report.json
Invalid records are never silently dropped: every rejection is recorded with its reasons.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ValidationError

from ml import config
from ml.ingestion import raw_store
from ml.ingestion.raw_store import Snapshot
from ml.validation.schema import (
    CAD_TO_INTERNAL,
    SBDB_TO_INTERNAL,
    CloseApproachRecord,
    NEORecord,
)

# CNEOS definition of a PHA (https://cneos.jpl.nasa.gov/about/neo_groups.html).
PHA_MOID_MAX_AU = 0.05
PHA_H_MAX = 22.0

NEO_STR_COLUMNS = ["designation", "full_name", "name", "condition_code", "orbit_class",
                   "first_obs_date", "last_obs_date"]
CAD_STR_COLUMNS = ["designation", "orbit_id", "time_uncertainty", "body"]


def _errors(exc: ValidationError) -> list[str]:
    return [f"{'.'.join(map(str, e['loc'])) or 'record'}: {e['msg']}" for e in exc.errors()]


def _validate_rows(
    snapshot: Snapshot,
    mapping: dict[str, str],
    model: type[BaseModel],
    key_field: str,
    extra: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = snapshot.payload()
    fields = payload["fields"]
    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row_number, row in enumerate(payload["data"]):
        if len(row) != len(fields):  # never truncate silently: reject and record
            rejected.append({"row": row_number, "key": None, "record": {"values": row},
                             "reasons": [f"record: expected {len(fields)} values, got {len(row)}"]})
            continue
        source = dict(zip(fields, row, strict=True))
        record = {mapping[k]: v for k, v in source.items() if k in mapping}
        record.update(extra or {})
        reasons: list[str] = []
        if source.get("neo", "Y") != "Y":  # SBDB query is filtered to NEOs; verify, don't assume
            reasons.append("neo: not flagged as NEO by source")
        try:
            parsed = model.model_validate(record)
        except ValidationError as exc:
            reasons += _errors(exc)
        else:
            if not reasons:
                valid.append(parsed.model_dump())
                continue
        rejected.append({"row": row_number, "key": record.get(key_field),
                         "reasons": reasons, "record": source})
    return valid, rejected


def validate_sbdb(snapshot: Snapshot) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    valid, rejected = _validate_rows(snapshot, SBDB_TO_INTERNAL, NEORecord, "spkid")
    df = pd.DataFrame(valid, columns=list(NEORecord.model_fields))
    df, dup_rejects = _reject_duplicates(df, ["spkid"], "spkid")
    df, dup_rejects2 = _reject_duplicates(df, ["designation"], "spkid")
    return df.reset_index(drop=True), rejected + dup_rejects + dup_rejects2


def validate_cad(
    snapshot: Snapshot, known_designations: set[str]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    valid, rejected = _validate_rows(
        snapshot, CAD_TO_INTERNAL, CloseApproachRecord, "designation",
        extra={"body": snapshot.meta["params"].get("body", config.CAD_BODY)},
    )
    df = pd.DataFrame(valid, columns=list(CloseApproachRecord.model_fields))
    df, dup_rejects = _reject_duplicates(df, ["designation", "approach_jd", "body"], "designation")
    orphan = ~df["designation"].isin(known_designations)
    rejected += [
        {"row": None, "key": r["designation"],
         "reasons": ["designation: not in validated NEO set (referential integrity)"],
         "record": {k: str(v) for k, v in r.items()}}
        for r in df[orphan].to_dict("records")
    ]
    return df[~orphan].reset_index(drop=True), rejected + dup_rejects


def _reject_duplicates(
    df: pd.DataFrame, subset: list[str], key: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    dup = df.duplicated(subset=subset, keep="first")
    rejects = [
        {"row": None, "key": r[key], "reasons": [f"duplicate {'+'.join(subset)}"],
         "record": {k: str(v) for k, v in r.items()}}
        for r in df[dup].to_dict("records")
    ]
    return df[~dup], rejects


def pha_rule_audit(df: pd.DataFrame) -> dict[str, Any]:
    """Empirically test the CNEOS PHA definition against JPL's flag (see docs/DATA_LEAKAGE.md)."""
    known = df[df["is_potentially_hazardous"].notna()]
    rule = (known["earth_moid_au"] <= PHA_MOID_MAX_AU) & (known["absolute_magnitude_h"] <= PHA_H_MAX)
    flag = known["is_potentially_hazardous"].astype(bool)
    return {
        "definition": f"earth_moid_au <= {PHA_MOID_MAX_AU} and absolute_magnitude_h <= {PHA_H_MAX}",
        "rows_with_flag": int(len(known)),
        "agree": int((rule == flag).sum()),
        "disagree": int((rule != flag).sum()),
        "flag_true_rule_false": int((flag & ~rule).sum()),
        "flag_false_rule_true": int((~flag & rule).sum()),
    }


def _summary(snapshot: Snapshot, valid: int, rejected: list[dict[str, Any]]) -> dict[str, Any]:
    reasons = Counter(r.split(":")[0] + ": " + r.split(": ", 1)[-1][:60]
                      for rej in rejected for r in rej["reasons"])
    return {
        "snapshot_file": snapshot.data_path.name,
        "sha256": snapshot.meta["sha256"],
        "retrieved_at": snapshot.meta["retrieved_at"],
        "api_version": snapshot.meta["api_version"],
        "params": snapshot.meta["params"],
        "raw_records": snapshot.meta["record_count"],
        "valid": valid,
        "rejected": len(rejected),
        "reject_reasons": dict(reasons),
    }


def dataset_version(snapshot: Snapshot) -> str:
    day = snapshot.meta["retrieved_at"][:10].replace("-", "")
    return f"jpl-sbdb-neo-{day}-{snapshot.meta['sha256'][:8]}"


def run(raw_dir: Path | None = None, interim_dir: Path | None = None) -> dict[str, Any]:
    interim_dir = interim_dir or config.INTERIM_DIR
    interim_dir.mkdir(parents=True, exist_ok=True)
    sbdb = raw_store.latest_snapshot(config.SBDB_SOURCE, raw_dir)
    cad = raw_store.latest_snapshot(config.CAD_SOURCE, raw_dir)
    if sbdb is None:
        raise FileNotFoundError("No SBDB snapshot found. Run: python -m ml.ingestion")

    neos, neo_rejects = validate_sbdb(sbdb)
    neos.to_csv(interim_dir / "neo_objects.csv", index=False)
    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_version": dataset_version(sbdb),
        "neo_objects": _summary(sbdb, len(neos), neo_rejects),
        "pha_rule_audit": pha_rule_audit(neos),
    }
    _write_jsonl(interim_dir / "rejected_neo_objects.jsonl", neo_rejects)

    if cad is not None:
        approaches, cad_rejects = validate_cad(cad, set(neos["designation"]))
        approaches.to_csv(interim_dir / "close_approaches.csv", index=False)
        _write_jsonl(interim_dir / "rejected_close_approaches.jsonl", cad_rejects)
        report["close_approaches"] = _summary(cad, len(approaches), cad_rejects)
        report["close_approaches"]["window"] = {
            "date_min": cad.meta["params"]["date-min"],
            "date_max": cad.meta["params"]["date-max"],
            "dist_max_au": float(cad.meta["params"]["dist-max"]),
            "body": cad.meta["params"]["body"],
        }
    (interim_dir / "validation_report.json").write_text(json.dumps(report, indent=2))
    return report


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str) + "\n")


# -- readers used by preprocessing and the database loader ---------------------
def load_interim_neos(interim_dir: Path | None = None) -> pd.DataFrame:
    path = (interim_dir or config.INTERIM_DIR) / "neo_objects.csv"
    dtypes: dict[str, str] = {c: "str" for c in NEO_STR_COLUMNS}
    dtypes["is_potentially_hazardous"] = "boolean"  # nullable: "True"/"False"/empty
    return pd.read_csv(path, dtype=dtypes, keep_default_na=False, na_values=[""],
                       low_memory=False)


def load_interim_approaches(interim_dir: Path | None = None) -> pd.DataFrame:
    path = (interim_dir or config.INTERIM_DIR) / "close_approaches.csv"
    return pd.read_csv(path, dtype={c: str for c in CAD_STR_COLUMNS},
                       keep_default_na=False, na_values=[""], parse_dates=["approach_time_tdb"])


def load_report(interim_dir: Path | None = None) -> dict[str, Any]:
    return json.loads(((interim_dir or config.INTERIM_DIR) / "validation_report.json").read_text())

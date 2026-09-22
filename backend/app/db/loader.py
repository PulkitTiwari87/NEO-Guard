"""Load validated interim data and model artifacts into the database.

Idempotent by design:
  * NEO objects are upserted on their SPK-ID (re-running updates, never duplicates);
  * close approaches from a CAD snapshot replace all approaches in that snapshot's window,
    so approaches whose orbit solution changed do not linger as stale duplicates;
  * data-source rows are unique per (source, snapshot checksum);
  * model rows keep their manually-set status when re-synced.
Each load runs in the caller's transaction; commit happens only if everything succeeded.
"""
from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import delete, func, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.models import CloseApproach, DataSource, Experiment, Model, NeoObject
from ml import artifacts, config
from ml.validation import validate

CHUNK = 500  # rows per statement: stays under SQLite/PostgreSQL bind-parameter limits


def _clean(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [{k: _clean(v) for k, v in rec.items()} for rec in df.to_dict("records")]


def _dialect_insert(db: Session):
    return pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert


def _upsert(db: Session, model: type, rows: list[dict[str, Any]], key: list[str]) -> None:
    for start in range(0, len(rows), CHUNK):
        stmt = _dialect_insert(db)(model).values(rows[start:start + CHUNK])
        update = {c: stmt.excluded[c] for c in rows[0] if c not in key}
        if "updated_at" in model.__table__.columns:
            update["updated_at"] = func.now()
        db.execute(stmt.on_conflict_do_update(index_elements=key, set_=update))


def register_source(
    db: Session, source_name: str, url: str, section: dict[str, Any], dataset_version: str | None
) -> DataSource:
    existing = db.scalar(select(DataSource).where(
        DataSource.source_name == source_name, DataSource.checksum == section["sha256"]))
    if existing:
        return existing
    source = DataSource(
        source_name=source_name, url=url, params=section["params"],
        retrieved_at=datetime.fromisoformat(section["retrieved_at"]),
        record_count=section["raw_records"], rejected_count=section["rejected"],
        schema_version=section["api_version"], dataset_version=dataset_version,
        checksum=section["sha256"],
    )
    db.add(source)
    db.flush()
    return source


def load_neo_objects(db: Session, df: pd.DataFrame, source_id: int) -> dict[str, int]:
    if df.empty:
        return {"inserted": 0, "updated": 0}
    existing = set(db.scalars(select(NeoObject.id)))
    rows = _records(df)
    for row in rows:
        row["id"] = row.pop("spkid")
        row["data_source_id"] = source_id
    inserted = sum(1 for r in rows if r["id"] not in existing)
    _upsert(db, NeoObject, rows, ["id"])
    return {"inserted": inserted, "updated": len(rows) - inserted}


def load_close_approaches(
    db: Session, df: pd.DataFrame, source_id: int, window: dict[str, Any]
) -> dict[str, int]:
    ids = dict(db.execute(select(NeoObject.designation, NeoObject.id)).all())
    lo = datetime.fromisoformat(window["date_min"])
    hi = datetime.fromisoformat(window["date_max"])
    deleted = db.execute(delete(CloseApproach).where(
        CloseApproach.body == window["body"],
        CloseApproach.approach_time_tdb >= lo,
        CloseApproach.approach_time_tdb <= hi,
    )).rowcount
    rows, skipped = [], 0
    for rec in _records(df):
        neo_id = ids.get(rec.pop("designation"))
        if neo_id is None:
            skipped += 1  # NEO not in the database: never invent a parent record
            continue
        rows.append({**rec, "neo_id": neo_id, "data_source_id": source_id})
    for start in range(0, len(rows), CHUNK):
        db.execute(insert(CloseApproach), rows[start:start + CHUNK])
    return {"inserted": len(rows), "replaced": deleted or 0, "skipped_unknown_object": skipped}


def load_interim(db: Session, interim_dir: Path | None = None) -> dict[str, Any]:
    interim_dir = interim_dir or config.INTERIM_DIR
    report = validate.load_report(interim_dir)
    neos = validate.load_interim_neos(interim_dir)
    source = register_source(db, config.SBDB_SOURCE, config.SBDB_URL, report["neo_objects"],
                             report["dataset_version"])
    result: dict[str, Any] = {"neo_objects": load_neo_objects(db, neos, source.id)}
    if "close_approaches" in report:
        cad = report["close_approaches"]
        cad_source = register_source(db, config.CAD_SOURCE, config.CAD_URL, cad, None)
        approaches = validate.load_interim_approaches(interim_dir)
        result["close_approaches"] = load_close_approaches(db, approaches, cad_source.id, cad["window"])
    db.commit()
    return result


def sync_models(db: Session, items: list[tuple[Path, dict[str, Any]]]) -> dict[str, int]:
    added = updated = 0
    for _, md in items:
        fields = {
            "name": md["model_name"], "algorithm": md["algorithm"],
            "artifact_path": md["artifact_path"], "dataset_version": md["dataset_version"],
            "feature_version": md["feature_version"], "threshold": md["threshold"],
            "parameters": md["parameters"], "metrics": md["metrics"], "features": md["features"],
            "split": md["split"], "created_at": datetime.fromisoformat(md["created_at"]),
        }
        model = db.scalar(select(Model).where(Model.version == md["model_version"]))
        if model is None:  # new rows start with the artifact's status (experimental)
            db.add(Model(version=md["model_version"], status=md.get("status", "experimental"), **fields))
            added += 1
        else:  # keep the status a human set
            for key, value in fields.items():
                setattr(model, key, value)
            updated += 1
        db.flush()
        experiment = db.scalar(select(Experiment).where(Experiment.experiment_id == md["experiment_id"]))
        if experiment is None:
            db.add(Experiment(
                experiment_id=md["experiment_id"], model_version=md["model_version"],
                dataset_version=md["dataset_version"], metrics=md["metrics"],
                config={k: md[k] for k in ("algorithm", "class_weight", "parameters", "random_seed",
                                           "threshold", "split", "libraries")},
                created_at=datetime.fromisoformat(md["created_at"]),
            ))
        else:
            experiment.metrics = md["metrics"]
    db.commit()
    return {"added": added, "updated": updated}


def set_model_status(db: Session, version: str, status: str) -> None:
    if status not in artifacts.STATUSES:
        raise ValueError(f"status must be one of {artifacts.STATUSES}")
    model = db.scalar(select(Model).where(Model.version == version))
    if model is None:
        raise LookupError(f"unknown model version {version!r} (run sync-models first)")
    model.status = status
    db.commit()

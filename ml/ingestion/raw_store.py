"""Write-once storage for raw API responses plus provenance metadata.

Layout: ``data/raw/<source>/<YYYY-MM-DD>/<source>_<UTC stamp>.json`` (response bytes verbatim)
and ``<source>_<UTC stamp>.meta.json`` (provenance). Files are opened in exclusive mode, so a
raw snapshot can never be overwritten.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ml import config
from ml.ingestion.jpl_client import FetchResult


@dataclass(frozen=True)
class Snapshot:
    meta: dict[str, Any]
    data_path: Path

    @property
    def meta_path(self) -> Path:
        return self.data_path.with_suffix(".meta.json")

    def payload(self) -> dict[str, Any]:
        return json.loads(self.data_path.read_bytes())


def save_snapshot(
    source: str, result: FetchResult, params: dict[str, str], raw_dir: Path | None = None
) -> Snapshot:
    raw_dir = raw_dir or config.RAW_DIR
    stamp = result.retrieved_at.strftime("%Y%m%dT%H%M%SZ")
    folder = raw_dir / source / result.retrieved_at.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    data_path = folder / f"{source}_{stamp}.json"
    with open(data_path, "xb") as fh:  # "x": never overwrite raw data
        fh.write(result.content)
    signature = result.payload.get("signature", {})
    meta = {
        "source": source,
        "endpoint": result.url.split("?")[0],
        "params": params,
        "retrieved_at": result.retrieved_at.isoformat(),
        "http_status": result.status,
        "api_version": signature.get("version"),
        "api_source": signature.get("source"),
        "record_count": len(result.payload["data"]),
        "fields": result.payload["fields"],
        "sha256": hashlib.sha256(result.content).hexdigest(),
        "data_file": data_path.name,
    }
    snapshot = Snapshot(meta, data_path)
    with open(snapshot.meta_path, "x", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return snapshot


def load_snapshot(meta_path: Path) -> Snapshot:
    meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    return Snapshot(meta, Path(meta_path).with_name(meta["data_file"]))


def list_snapshots(source: str, raw_dir: Path | None = None) -> list[Snapshot]:
    """All snapshots for a source, oldest first."""
    folder = (raw_dir or config.RAW_DIR) / source
    snapshots = [load_snapshot(p) for p in sorted(folder.glob("*/*.meta.json"))]
    return sorted(snapshots, key=lambda s: s.meta["retrieved_at"])


def latest_snapshot(source: str, raw_dir: Path | None = None) -> Snapshot | None:
    snapshots = list_snapshots(source, raw_dir)
    return snapshots[-1] if snapshots else None


def find_recent(
    source: str, params: dict[str, str], max_age: timedelta, raw_dir: Path | None = None
) -> Snapshot | None:
    """Newest snapshot with identical query params that is younger than ``max_age`` (cache hit)."""
    cutoff = datetime.now(UTC) - max_age
    for snapshot in reversed(list_snapshots(source, raw_dir)):
        if snapshot.meta["params"] != params:
            continue
        if datetime.fromisoformat(snapshot.meta["retrieved_at"]) >= cutoff:
            return snapshot
    return None

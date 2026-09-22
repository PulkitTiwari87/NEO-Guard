"""SYNTHETIC / TEST DATA generators. TEST FIXTURE - NOT NASA PRODUCTION DATA.

Everything produced here is randomly generated for tests. Designations are ``TEST-#####`` and the
JSON envelopes carry ``_fixture_notice``. The "PHA" label below is a made-up rule that gives the
models something learnable; it is NOT the real physics and NOT JPL's flag.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from ml import config
from ml.evaluation import evaluate
from ml.explainability import explain
from ml.ingestion import raw_store
from ml.ingestion.jpl_client import FetchResult, cad_params, sbdb_params
from ml.preprocessing import dataset
from ml.training import train
from ml.validation import validate

NOTICE = "SYNTHETIC / TEST DATA - TEST FIXTURE, NOT NASA PRODUCTION DATA"
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CAD_FIELDS = ["des", "orbit_id", "jd", "cd", "dist", "dist_min", "dist_max", "v_rel", "v_inf",
              "t_sigma_f", "h"]


def _g(x: float) -> str:
    return f"{x:.8g}"


def synthetic_sbdb_payload(n: int = 3000, seed: int = 7) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        q = rng.uniform(0.4, 1.29)
        e = rng.uniform(0.05, 0.9)
        a = q / (1 - e)
        h = rng.normal(22.5, 2.0)
        inc = rng.uniform(0, 60)
        moid = abs(q - 1.0) * 0.8 + abs(rng.normal(0, 0.02)) + inc / 600  # synthetic stand-in
        year = int(rng.integers(2000, 2026))
        rec = {
            "spkid": 20000000 + i, "pdes": f"TEST-{i:05d}", "full_name": f"  TEST-{i:05d} (SYNTH)",
            "name": None, "neo": "Y", "pha": "Y" if (moid <= 0.05 and h <= 22.0) else "N",
            "H": _g(h), "diameter": None, "albedo": None, "e": _g(e), "a": _g(a), "q": _g(q),
            "ad": _g(a * (1 + e)), "i": _g(inc), "om": _g(rng.uniform(0, 360)),
            "w": _g(rng.uniform(0, 360)), "ma": _g(rng.uniform(0, 360)), "n": "0.5", "per": "500",
            "moid": _g(moid), "epoch": "2461200.5", "condition_code": "0",
            "first_obs": f"{year}-06-15", "last_obs": "2026-01-01", "n_obs_used": 100,
            "data_arc": "1000", "rms": ".3", "class": "APO",
        }
        rows.append([rec[f] for f in config.SBDB_FIELDS])
    return {"_fixture_notice": NOTICE,
            "signature": {"source": "SYNTHETIC / TEST DATA (not JPL)", "version": "test"},
            "fields": list(config.SBDB_FIELDS), "data": rows, "count": len(rows)}


def synthetic_cad_payload(sbdb: dict[str, Any], n_objects: int = 200, seed: int = 11) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    pdes_idx = sbdb["fields"].index("pdes")
    rows = []
    for row in sbdb["data"][:n_objects]:
        for _ in range(int(rng.integers(1, 4))):
            dist = rng.uniform(0.001, 0.049)
            year, month, day = int(rng.integers(2020, 2031)), int(rng.integers(1, 13)), int(rng.integers(1, 28))
            rows.append([
                row[pdes_idx], "1", f"{2458849.5 + rng.uniform(0, 3650):.9f}",
                f"{year}-{_MONTHS[month - 1]}-{day:02d} 12:30", _g(dist), _g(dist * 0.9),
                _g(dist * 1.1), _g(rng.uniform(1, 30)), _g(rng.uniform(1, 30)), "00:05", "22.5",
            ])
    return {"_fixture_notice": NOTICE,
            "signature": {"source": "SYNTHETIC / TEST DATA (not JPL)", "version": "test"},
            "fields": CAD_FIELDS, "data": rows, "count": len(rows)}


def fetch_result(payload: dict[str, Any], url: str = "https://synthetic.invalid/test") -> FetchResult:
    return FetchResult(url=url, status=200, content=json.dumps(payload).encode(), payload=payload,
                       retrieved_at=datetime.now(UTC))


def build_workspace(root: Path) -> dict[str, Any]:
    """Run the whole pipeline on synthetic data inside ``root`` (never touches data/ or ml/artifacts)."""
    raw, interim, processed = root / "raw", root / "interim", root / "processed"
    artifacts_dir, log_doc = root / "artifacts", root / "EXPERIMENTS.md"
    log_doc.write_text("# Experiments Log (SYNTHETIC / TEST DATA)\n", encoding="utf-8")

    sbdb = synthetic_sbdb_payload()
    cad = synthetic_cad_payload(sbdb)
    raw_store.save_snapshot(config.SBDB_SOURCE, fetch_result(sbdb, config.SBDB_URL), sbdb_params(), raw)
    raw_store.save_snapshot(
        config.CAD_SOURCE, fetch_result(cad, config.CAD_URL),
        cad_params(config.CAD_DATE_MIN, config.CAD_DATE_MAX, config.CAD_DIST_MAX_AU), raw)

    report = validate.run(raw, interim)
    manifest = dataset.run(interim, processed)
    train.run(train.ALGORITHMS, train.CLASS_WEIGHTS, processed, artifacts_dir)
    evaluate.run(processed_dir=processed, artifacts_root=artifacts_dir, log_doc=log_doc)
    explain.run(processed_dir=processed, artifacts_root=artifacts_dir)
    return {"raw_dir": raw, "interim_dir": interim, "processed_dir": processed,
            "artifacts_dir": artifacts_dir, "log_doc": log_doc, "report": report,
            "manifest": manifest, "sbdb": sbdb, "cad": cad}

"""Validation and normalisation: rejects bad records with reasons, never drops silently."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest
from pydantic import ValidationError

from ml.ingestion import raw_store
from ml.ingestion.jpl_client import cad_params, sbdb_params
from ml.validation import validate
from ml.validation.schema import CloseApproachRecord, NEORecord
from tests.helpers import fetch_result, synthetic_cad_payload, synthetic_sbdb_payload


def good(**override):
    """A valid SYNTHETIC / TEST DATA record in the internal schema (q = a(1-e), Q = a(1+e))."""
    record = dict(
        spkid=1, designation="TEST-1", full_name="TEST-1", name=None, is_potentially_hazardous=False,
        absolute_magnitude_h=22.0, diameter_km=None, albedo=None, eccentricity=0.5,
        semi_major_axis_au=1.2, perihelion_distance_au=0.6, aphelion_distance_au=1.8,
        inclination_deg=10.0, ascending_node_deg=100.0, argument_of_perihelion_deg=50.0,
        mean_anomaly_deg=10.0, mean_motion_deg_per_day=0.9, orbital_period_days=500.0,
        earth_moid_au=0.1, epoch_jd=2461200.5, condition_code="0", first_obs_date="2010-05-01",
        last_obs_date="2020-01-01", n_obs_used=50, data_arc_days=100, rms=0.3, orbit_class="APO",
    )
    record.update(override)
    return record


def test_valid_record_is_accepted():
    rec = NEORecord.model_validate(good())
    assert rec.first_obs_year == 2010 and rec.is_potentially_hazardous is False


@pytest.mark.parametrize("override", [
    {"eccentricity": -0.1},
    {"eccentricity": 1.2},  # unbound orbit is out of scope
    {"perihelion_distance_au": 0.9},  # inconsistent with a(1-e)
    {"aphelion_distance_au": 5.0},  # inconsistent with a(1+e)
    {"inclination_deg": 181.0},
    {"ascending_node_deg": 361.0},
    {"semi_major_axis_au": 3.0, "perihelion_distance_au": 1.5, "aphelion_distance_au": 4.5},  # q > 1.3
    {"is_potentially_hazardous": "maybe"},
    {"spkid": 0},
    {"diameter_km": 0.0},
    {"earth_moid_au": -1.0},
    {"designation": ""},
    {"unexpected_field": 1},
])
def test_invalid_records_are_rejected(override):
    with pytest.raises(ValidationError):
        NEORecord.model_validate(good(**override))


def test_year_is_derived_even_when_month_and_day_are_unknown():
    assert NEORecord.model_validate(good(first_obs_date="2008-??-??")).first_obs_year == 2008


@pytest.mark.parametrize("flag, expected", [("Y", True), ("N", False), (None, None)])
def test_pha_flag_mapping(flag, expected):
    assert NEORecord.model_validate(good(is_potentially_hazardous=flag)).is_potentially_hazardous is expected


def cad(**override):
    record = dict(designation="TEST-1", orbit_id="1", approach_jd=2458849.5,
                  approach_time_tdb="2026-Sep-01 02:53", distance_au=0.02, distance_min_au=0.018,
                  distance_max_au=0.022, v_rel_km_s=10.0, v_inf_km_s=None, time_uncertainty="00:05",
                  absolute_magnitude_h=22.5, body="Earth")
    record.update(override)
    return record


def test_cad_date_is_parsed_and_bounds_checked():
    assert CloseApproachRecord.model_validate(cad()).approach_time_tdb == datetime(2026, 9, 1, 2, 53)
    for bad in ({"approach_time_tdb": "2026-Foo-01 02:53"}, {"distance_min_au": 0.5}, {"v_rel_km_s": -1.0}):
        with pytest.raises(ValidationError):
            CloseApproachRecord.model_validate(cad(**bad))


def snapshot(tmp_path, payload, source="jpl_sbdb", params=None):
    return raw_store.save_snapshot(source, fetch_result(payload), params or sbdb_params(), tmp_path)


def test_invalid_rows_are_recorded_with_reasons_never_dropped_silently(tmp_path):
    payload = synthetic_sbdb_payload(n=20)
    idx = {name: payload["fields"].index(name) for name in ("e", "neo", "pdes")}
    payload["data"][3][idx["e"]] = "-0.5"
    payload["data"][5][idx["neo"]] = "N"
    payload["data"][7][idx["pdes"]] = payload["data"][6][idx["pdes"]]  # duplicate designation
    valid, rejected = validate.validate_sbdb(snapshot(tmp_path, payload))
    assert len(valid) + len(rejected) == 20
    reasons = {r["key"]: " | ".join(r["reasons"]) for r in rejected}
    assert "eccentricity" in reasons[20000003]
    assert "not flagged as NEO" in reasons[20000005]
    assert "duplicate designation" in reasons[20000007]
    assert all(r["record"] for r in rejected)  # the original source row is kept for review


def test_rows_with_the_wrong_number_of_values_are_rejected_not_truncated(tmp_path):
    payload = synthetic_sbdb_payload(n=5)
    payload["data"][2] = payload["data"][2][:-3]  # malformed source row
    valid, rejected = validate.validate_sbdb(snapshot(tmp_path, payload))
    assert len(valid) == 4 and len(rejected) == 1
    assert "expected" in rejected[0]["reasons"][0] and rejected[0]["row"] == 2


def test_close_approaches_of_unknown_objects_are_rejected(tmp_path):
    sbdb = synthetic_sbdb_payload(n=20)
    cad_snap = snapshot(tmp_path, synthetic_cad_payload(sbdb, n_objects=10), "jpl_cad",
                        cad_params("2000-01-01", "2100-01-01", 0.05))
    known = {row[1] for row in sbdb["data"][:2]}
    valid, rejected = validate.validate_cad(cad_snap, known)
    assert set(valid["designation"]) <= known
    assert rejected and all("not in validated NEO set" in r["reasons"][0] for r in rejected)


def test_pha_rule_audit_counts_agreement_and_both_kinds_of_disagreement():
    df = pd.DataFrame({
        "earth_moid_au": [0.01, 0.10, 0.01, 0.01, None],
        "absolute_magnitude_h": [20.0, 20.0, 23.0, 20.0, 20.0],
        "is_potentially_hazardous": pd.array([True, False, True, False, None], dtype="boolean"),
    })
    audit = validate.pha_rule_audit(df)
    assert audit["rows_with_flag"] == 4 and audit["agree"] == 2 and audit["disagree"] == 2
    assert audit["flag_true_rule_false"] == 1 and audit["flag_false_rule_true"] == 1


def test_run_writes_interim_files_and_report(workspace):
    report, interim = workspace["report"], workspace["interim_dir"]
    assert report["neo_objects"]["valid"] == 3000 and report["neo_objects"]["rejected"] == 0
    assert report["neo_objects"]["sha256"] and report["dataset_version"].startswith("jpl-sbdb-neo-")
    assert report["pha_rule_audit"]["rows_with_flag"] == 3000
    for name in ("neo_objects.csv", "close_approaches.csv", "rejected_neo_objects.jsonl",
                 "validation_report.json"):
        assert (interim / name).exists()


def test_interim_round_trip_preserves_types(workspace):
    neos = validate.load_interim_neos(workspace["interim_dir"])
    assert str(neos["is_potentially_hazardous"].dtype) == "boolean"
    assert neos["designation"].iloc[0] == "TEST-00000" and neos["name"].isna().all()
    approaches = validate.load_interim_approaches(workspace["interim_dir"])
    assert pd.api.types.is_datetime64_any_dtype(approaches["approach_time_tdb"])

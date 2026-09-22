"""Database loader: idempotent upserts, window replacement, registry sync. SYNTHETIC / TEST DATA."""
from __future__ import annotations

import shutil

import pytest
from app.db import loader
from app.db.models import CloseApproach, DataSource, Experiment, Model, NeoObject
from sqlalchemy import func, select

from ml import artifacts
from ml.validation import validate


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_first_load_inserts_everything_with_provenance(session_factory, workspace):
    n_cad = workspace["report"]["close_approaches"]["valid"]
    with session_factory() as db:
        result = loader.load_interim(db, workspace["interim_dir"])
        assert result["neo_objects"] == {"inserted": 3000, "updated": 0}
        assert result["close_approaches"] == {"inserted": n_cad, "replaced": 0, "skipped_unknown_object": 0}
        assert count(db, NeoObject) == 3000 and count(db, CloseApproach) == n_cad
        sources = {s.source_name: s for s in db.scalars(select(DataSource))}
        assert set(sources) == {"jpl_sbdb", "jpl_cad"} and len(sources["jpl_sbdb"].checksum) == 64
        assert db.get(NeoObject, 20000000).data_source_id == sources["jpl_sbdb"].id


def test_loading_twice_does_not_duplicate_anything(session_factory, workspace):
    with session_factory() as db:
        loader.load_interim(db, workspace["interim_dir"])
        second = loader.load_interim(db, workspace["interim_dir"])
        assert second["neo_objects"] == {"inserted": 0, "updated": 3000}
        assert second["close_approaches"]["replaced"] == second["close_approaches"]["inserted"]
        assert count(db, NeoObject) == 3000 and count(db, DataSource) == 2
        assert count(db, CloseApproach) == workspace["report"]["close_approaches"]["valid"]


def test_changed_source_values_update_in_place_without_stale_rows(session_factory, workspace, tmp_path):
    interim = tmp_path / "interim"
    shutil.copytree(workspace["interim_dir"], interim)
    with session_factory() as db:
        loader.load_interim(db, workspace["interim_dir"])
        approaches = validate.load_interim_approaches(interim)
        old = approaches.loc[0, "distance_au"]
        approaches.loc[0, ["distance_au", "distance_min_au", "distance_max_au"]] = [0.0123, 0.012, 0.013]
        approaches.to_csv(interim / "close_approaches.csv", index=False)
        neos = validate.load_interim_neos(interim)
        neos.loc[0, "absolute_magnitude_h"] = 19.5
        neos.to_csv(interim / "neo_objects.csv", index=False)

        loader.load_interim(db, interim)
        assert count(db, CloseApproach) == len(approaches)
        assert db.get(NeoObject, int(neos.loc[0, "spkid"])).absolute_magnitude_h == 19.5
        distances = set(db.scalars(select(CloseApproach.distance_au)))
        assert 0.0123 in distances and old not in distances


def test_approaches_of_unknown_objects_are_skipped_not_invented(session_factory, workspace):
    with session_factory() as db:
        loader.load_interim(db, workspace["interim_dir"])
        orphan = validate.load_interim_approaches(workspace["interim_dir"]).head(1).copy()
        orphan["designation"] = "NOT-IN-DB"
        empty_window = {"date_min": "1900-01-01", "date_max": "1900-01-02", "body": "Earth"}
        result = loader.load_close_approaches(db, orphan, 1, empty_window)
        assert result == {"inserted": 0, "replaced": 0, "skipped_unknown_object": 1}
        assert count(db, NeoObject) == 3000


def test_model_sync_registers_and_never_overwrites_a_human_set_status(session_factory, workspace):
    items = artifacts.list_artifacts(workspace["artifacts_dir"])
    with session_factory() as db:
        assert loader.sync_models(db, items) == {"added": 6, "updated": 0}
        assert {m.status for m in db.scalars(select(Model))} == {"experimental"}
        loader.set_model_status(db, "xgboost-v1", "validated")
        assert loader.sync_models(db, items) == {"added": 0, "updated": 6}
        assert db.scalar(select(Model.status).where(Model.version == "xgboost-v1")) == "validated"
        assert count(db, Experiment) == 6
        row = db.scalar(select(Model).where(Model.version == "random_forest-v1"))
        assert row.artifact_path == "random_forest/v1" and set(row.metrics) == {"validation", "test"}


def test_status_changes_are_validated(session_factory, workspace):
    with session_factory() as db:
        loader.sync_models(db, artifacts.list_artifacts(workspace["artifacts_dir"]))
        with pytest.raises(ValueError, match="status must be one of"):
            loader.set_model_status(db, "xgboost-v1", "best-ever")
        with pytest.raises(LookupError, match="unknown model version"):
            loader.set_model_status(db, "ghost-v9", "production")


def test_missing_values_are_stored_as_null_and_integers_stay_integers(session_factory, workspace):
    with session_factory() as db:
        loader.load_interim(db, workspace["interim_dir"])
        neo = db.get(NeoObject, 20000000)
        assert neo.name is None and neo.diameter_km is None and neo.albedo is None
        assert neo.data_arc_days == 1000 and isinstance(neo.n_obs_used, int)

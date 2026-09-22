"""Leakage guards: the model may only see audited, non-target-defining, pre-outcome features."""
from __future__ import annotations

import numpy as np
from app.db.models import NeoObject
from sklearn.metrics import average_precision_score
from sklearn.tree import DecisionTreeClassifier

from ml import artifacts, config
from ml.features.audit import FEATURE_AUDIT, audited_features
from ml.preprocessing import dataset
from ml.validation import validate
from ml.validation.schema import NEORecord

TARGET_DEFINING = {"absolute_magnitude_h", "earth_moid_au"}  # PHA := MOID <= 0.05 au and H <= 22.0
SIZE_PROXIES = {"diameter_km", "albedo"}
POST_OUTCOME = {"n_obs_used", "data_arc_days", "condition_code", "rms", "last_obs_date"}


def test_every_record_column_has_an_audit_entry():
    assert set(NEORecord.model_fields) == set(FEATURE_AUDIT)


def test_model_inputs_are_exactly_the_audited_features():
    assert set(config.RAW_FEATURES) == audited_features()


def test_target_definition_and_size_proxies_are_never_inputs():
    banned = TARGET_DEFINING | SIZE_PROXIES | {config.TARGET}
    assert banned.isdisjoint(config.RAW_FEATURES)
    for column in banned:
        assert FEATURE_AUDIT[column][0] in {"excluded", "target"}
    assert not any(w in name for name in config.FEATURE_COLUMNS for w in ("moid", "magnitude", "diameter"))


def test_post_outcome_observation_metadata_is_excluded():
    assert all(FEATURE_AUDIT[c][0] == "excluded" for c in POST_OUTCOME)
    assert POST_OUTCOME.isdisjoint(config.RAW_FEATURES)


def test_columns_used_only_for_splitting_are_not_features():
    split_only = {c for c, (status, _) in FEATURE_AUDIT.items() if status == "split_only"}
    assert split_only == {"first_obs_date", "first_obs_year"}
    assert split_only.isdisjoint(config.RAW_FEATURES)


def test_database_schema_mirrors_the_internal_schema():
    expected = (set(NEORecord.model_fields) - {"spkid"}) | {"id", "data_source_id", "created_at", "updated_at"}
    assert {c.name for c in NeoObject.__table__.columns} == expected


def test_trained_artifacts_use_only_audited_features(workspace):
    items = artifacts.list_artifacts(workspace["artifacts_dir"])
    assert len(items) == 6
    for _, md in items:
        assert set(md["raw_features"]) <= audited_features()
        assert md["raw_features"] == config.RAW_FEATURES and md["features"] == config.FEATURE_COLUMNS


def test_processed_dataset_contains_no_target_defining_columns(workspace):
    columns = set(dataset.load_dataset(workspace["processed_dir"]).columns)
    assert columns.isdisjoint(TARGET_DEFINING | SIZE_PROXIES | POST_OUTCOME)


def test_split_has_no_temporal_or_identity_leakage(workspace):
    data = dataset.load_dataset(workspace["processed_dir"])
    years = {s: data.loc[data["split"] == s, "first_obs_year"] for s in dataset.SPLITS}
    assert years["train"].max() < years["validation"].min() <= years["validation"].max() < years["test"].min()
    assert not data["spkid"].duplicated().any()
    assert not data.duplicated(subset=config.RAW_FEATURES).any()
    assert workspace["manifest"]["cross_split_duplicate_feature_vectors"] == 0


def test_canary_target_defining_features_would_make_the_task_trivial(workspace):
    """Why the exclusion matters: with H and MOID a tree re-derives the label almost perfectly."""
    interim = validate.load_interim_neos(workspace["interim_dir"])
    data = dataset.load_dataset(workspace["processed_dir"])[["spkid", "split"]]
    df = interim.merge(data, on="spkid").dropna(subset=["earth_moid_au", "absolute_magnitude_h"])
    y = df[config.TARGET].astype(int)
    train, test = df["split"] == "train", df["split"] == "test"

    def average_precision(columns: list[str]) -> float:
        tree = DecisionTreeClassifier(max_depth=6, random_state=config.RANDOM_SEED)
        tree.fit(df.loc[train, columns], y[train])
        return average_precision_score(y[test], tree.predict_proba(df.loc[test, columns])[:, 1])

    leaked = average_precision(["earth_moid_au", "absolute_magnitude_h"])
    clean = average_precision(config.RAW_FEATURES)
    assert leaked > 0.99
    assert np.isfinite(clean) and clean < 0.9

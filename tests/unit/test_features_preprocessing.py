"""Feature engineering and the chronological split. Uses SYNTHETIC / TEST DATA."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml import config
from ml.features.engineering import build_features
from ml.preprocessing import dataset


def raw_frame(**override) -> pd.DataFrame:
    data = {c: [1.0, 2.0] for c in config.RAW_FEATURES}
    data.update(override)
    return pd.DataFrame(data)


def test_feature_columns_and_order_match_config():
    assert list(build_features(raw_frame()).columns) == config.FEATURE_COLUMNS


def test_angles_are_encoded_on_the_circle():
    out = build_features(raw_frame(ascending_node_deg=[90.0, 0.0], argument_of_perihelion_deg=[180.0, 360.0]))
    assert out["ascending_node_sin"].iloc[0] == pytest.approx(1.0)
    assert out["ascending_node_cos"].iloc[0] == pytest.approx(0.0, abs=1e-12)
    assert out["argument_of_perihelion_cos"].iloc[0] == pytest.approx(-1.0)
    assert out["argument_of_perihelion_cos"].iloc[1] == pytest.approx(1.0)  # 360 deg == 0 deg


def test_features_are_finite_stateless_and_do_not_mutate_input():
    raw = raw_frame()
    before = raw.copy()
    first, second = build_features(raw), build_features(raw)
    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(raw, before)
    assert np.isfinite(first.to_numpy()).all()


def test_missing_input_column_is_an_error():
    with pytest.raises(ValueError, match="missing input columns"):
        build_features(raw_frame().drop(columns=["eccentricity"]))


def neos(n=1000, seed=3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({c: rng.uniform(0.1, 100, n) for c in config.RAW_FEATURES})
    df["spkid"] = np.arange(n) + 1
    df["designation"] = [f"TEST-{i}" for i in range(n)]
    df["first_obs_year"] = rng.integers(2000, 2026, n)
    df[config.TARGET] = pd.array(rng.random(n) < 0.1, dtype="boolean")
    return df


def test_temporal_cutoffs_assign_whole_years():
    years = pd.Series([2000] * 70 + [2001] * 15 + [2002] * 15)
    assert dataset.temporal_cutoffs(years, config.SPLIT_FRACTIONS) == (2000, 2001)
    with pytest.raises(ValueError, match="three non-empty"):
        dataset.temporal_cutoffs(pd.Series([2000] * 50 + [2001] * 50), config.SPLIT_FRACTIONS)


def test_split_is_strictly_chronological_and_disjoint():
    df, stats = dataset.build_dataset(neos())
    by = {s: df[df["split"] == s] for s in dataset.SPLITS}
    assert by["train"]["first_obs_year"].max() < by["validation"]["first_obs_year"].min()
    assert by["validation"]["first_obs_year"].max() < by["test"]["first_obs_year"].min()
    assert not df["spkid"].duplicated().any()
    assert stats["cross_split_duplicate_feature_vectors"] == 0 and stats["cross_split_spkid_overlap"] == 0
    assert sum(s["rows"] for s in stats["splits"].values()) == len(df)


def test_ineligible_and_duplicate_rows_are_excluded_and_counted():
    df = neos(200)
    df.loc[0, config.TARGET] = pd.NA  # unknown label
    df.loc[1, "eccentricity"] = np.nan  # incomplete features
    df.loc[3, config.RAW_FEATURES] = df.loc[2, config.RAW_FEATURES].to_numpy()  # duplicate vector
    out, stats = dataset.build_dataset(df)
    assert stats["excluded_missing_target"] == 1
    assert stats["excluded_missing_features"] == 1
    assert stats["excluded_duplicate_feature_vectors"] == 1
    assert len(out) == 197 and set(out[config.TARGET]) <= {0, 1}


def test_processed_dataset_has_only_expected_columns(workspace):
    data = dataset.load_dataset(workspace["processed_dir"])
    assert list(data.columns) == dataset.OUTPUT_COLUMNS
    assert workspace["manifest"]["class_distribution"]["positives"] == int(data[config.TARGET].sum())

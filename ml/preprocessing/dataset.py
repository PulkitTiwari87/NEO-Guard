"""Build the ML dataset from data/interim/neo_objects.csv.

Steps (in order, all before any model or scaler is fitted):
  1. keep ML-eligible rows: known PHA flag and complete orbital features;
  2. drop duplicate feature vectors (duplicate-leakage guard);
  3. assign a chronological split by the year of the first observation.
Nothing here learns parameters from data, so the split cannot leak statistics.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ml import config
from ml.validation import validate

SPLITS = ("train", "validation", "test")
OUTPUT_COLUMNS = ["spkid", "designation", "first_obs_year", "split", *config.RAW_FEATURES,
                  config.TARGET]


def temporal_cutoffs(years: pd.Series, fractions: dict[str, float]) -> tuple[int, int]:
    """Last year of train and of validation: smallest year reaching the cumulative fraction.

    Whole years are assigned to a single split, so objects sharing a first-observation year
    are never separated and the split is strictly chronological.
    """
    counts = years.value_counts().sort_index()
    cumulative = counts.cumsum() / counts.sum()
    train_end = int(cumulative[cumulative >= fractions["train"]].index[0])
    val_end = int(cumulative[cumulative >= fractions["train"] + fractions["validation"]].index[0])
    if val_end <= train_end or val_end >= int(counts.index[-1]):
        raise ValueError("Cannot form three non-empty chronological splits from this data")
    return train_end, val_end


def assign_split(years: pd.Series, train_end: int, val_end: int) -> pd.Series:
    split = pd.Series("test", index=years.index)
    split[years <= val_end] = "validation"
    split[years <= train_end] = "train"
    return split


def build_dataset(neos: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    stats: dict[str, Any] = {"input_rows": int(len(neos))}
    df = neos

    no_target = df[config.TARGET].isna()
    incomplete = df[config.RAW_FEATURES].isna().any(axis=1)
    stats["excluded_missing_target"] = int(no_target.sum())
    stats["excluded_missing_features"] = int((incomplete & ~no_target).sum())
    df = df[~(no_target | incomplete)]

    duplicate = df.duplicated(subset=config.RAW_FEATURES, keep="first")
    stats["excluded_duplicate_feature_vectors"] = int(duplicate.sum())
    df = df[~duplicate].copy()

    train_end, val_end = temporal_cutoffs(df["first_obs_year"], config.SPLIT_FRACTIONS)
    df["split"] = assign_split(df["first_obs_year"], train_end, val_end)
    df[config.TARGET] = df[config.TARGET].astype(bool).astype(int)
    df = df[OUTPUT_COLUMNS].sort_values(["first_obs_year", "spkid"]).reset_index(drop=True)

    stats["cutoffs"] = {"train_last_year": train_end, "validation_last_year": val_end}
    stats["rows"] = int(len(df))
    stats["splits"] = {
        s: {
            "rows": int((df["split"] == s).sum()),
            "positives": int(df.loc[df["split"] == s, config.TARGET].sum()),
            "positive_rate": float(df.loc[df["split"] == s, config.TARGET].mean()),
            "first_obs_year_min": int(df.loc[df["split"] == s, "first_obs_year"].min()),
            "first_obs_year_max": int(df.loc[df["split"] == s, "first_obs_year"].max()),
        }
        for s in SPLITS
    }
    stats["class_distribution"] = {
        "positives": int(df[config.TARGET].sum()),
        "negatives": int((1 - df[config.TARGET]).sum()),
        "positive_rate": float(df[config.TARGET].mean()),
    }
    n_splits_per_vector = df.groupby(config.RAW_FEATURES)["split"].nunique()
    stats["cross_split_duplicate_feature_vectors"] = int((n_splits_per_vector > 1).sum())
    stats["cross_split_spkid_overlap"] = int(df["spkid"].duplicated().sum())
    return df, stats


def run(interim_dir: Path | None = None, processed_dir: Path | None = None) -> dict[str, Any]:
    interim_dir = interim_dir or config.INTERIM_DIR
    processed_dir = processed_dir or config.PROCESSED_DIR
    processed_dir.mkdir(parents=True, exist_ok=True)
    neos = validate.load_interim_neos(interim_dir)
    report = validate.load_report(interim_dir)
    dataset, stats = build_dataset(neos)
    dataset.to_csv(processed_dir / "neo_ml_dataset.csv", index=False)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_version": report["dataset_version"],
        "feature_version": config.FEATURE_VERSION,
        "target": config.TARGET,
        "target_definition": "JPL SBDB 'pha' flag: Earth MOID <= 0.05 au and H <= 22.0 (CNEOS)",
        "split_method": "chronological by first_obs_year (whole years per split)",
        "split_fractions_requested": config.SPLIT_FRACTIONS,
        "raw_features": config.RAW_FEATURES,
        "interim_sha256": hashlib.sha256((interim_dir / "neo_objects.csv").read_bytes()).hexdigest(),
        **stats,
    }
    (processed_dir / "split_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def load_dataset(processed_dir: Path | None = None) -> pd.DataFrame:
    path = (processed_dir or config.PROCESSED_DIR) / "neo_ml_dataset.csv"
    return pd.read_csv(path, dtype={"designation": str})


def load_manifest(processed_dir: Path | None = None) -> dict[str, Any]:
    return json.loads(((processed_dir or config.PROCESSED_DIR) / "split_manifest.json").read_text())

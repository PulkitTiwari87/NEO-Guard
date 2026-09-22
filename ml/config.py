"""Shared constants and paths for the data/ML pipeline.

Anything scientific (feature lists, thresholds) is documented in docs/DATA_LEAKAGE.md
and docs/FEATURE_POLICY.md. Change those documents together with this file.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("NEOGUARD_DATA_DIR", REPO_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = Path(os.environ.get("MODEL_DIR", REPO_ROOT / "ml" / "artifacts"))
EXPERIMENTS_DOC = REPO_ROOT / "docs" / "EXPERIMENTS.md"

RANDOM_SEED = 42

# --- JPL sources (see docs/DATA_SOURCE.md) -----------------------------------
SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
SBDB_SOURCE = "jpl_sbdb"
CAD_SOURCE = "jpl_cad"

# Source field names requested from the SBDB Query API. Mapped to internal names in
# ml/validation/schema.py.
SBDB_FIELDS = [
    "spkid", "pdes", "full_name", "name", "neo", "pha", "H", "diameter", "albedo",
    "e", "a", "q", "ad", "i", "om", "w", "ma", "n", "per", "moid", "epoch",
    "condition_code", "first_obs", "last_obs", "n_obs_used", "data_arc", "rms", "class",
]

# Default close-approach query window / limits (documented choice, overridable on the CLI).
CAD_DATE_MIN = "2000-01-01"
CAD_DATE_MAX = "2100-01-01"
CAD_DIST_MAX_AU = 0.05  # = the PHA MOID threshold; keeps the table to genuinely close passes
CAD_BODY = "Earth"

AU_KM = 149_597_870.7  # IAU 2012 exact definition of the astronomical unit

# --- ML target / features (see docs/DATA_LEAKAGE.md) ------------------------
TARGET = "is_potentially_hazardous"
FEATURE_VERSION = "features-v1"

# Columns fed to the model pipeline. All are orbital elements published by SBDB.
RAW_FEATURES = [
    "semi_major_axis_au",
    "eccentricity",
    "inclination_deg",
    "perihelion_distance_au",
    "aphelion_distance_au",
    "ascending_node_deg",
    "argument_of_perihelion_deg",
]
# Columns produced by ml.features.engineering.build_features (the model's actual inputs).
FEATURE_COLUMNS = [
    "semi_major_axis_au",
    "eccentricity",
    "inclination_deg",
    "perihelion_distance_au",
    "aphelion_distance_au",
    "ascending_node_sin",
    "ascending_node_cos",
    "argument_of_perihelion_sin",
    "argument_of_perihelion_cos",
]

# Chronological split on discovery-era: year of the first observation in the orbit fit.
SPLIT_FRACTIONS = {"train": 0.70, "validation": 0.15, "test": 0.15}

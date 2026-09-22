"""Stateless feature engineering (identical at training and prediction time).

Derived features (documented in docs/FEATURE_POLICY.md):
  <angle>_sin = sin(radians(angle)), <angle>_cos = cos(radians(angle))
for the longitude of the ascending node and the argument of perihelion. Rationale: these are
angles on a circle (0 deg == 360 deg); raw degrees would put 359 deg and 1 deg far apart.
The transform has no fitted state, so it cannot leak information from the test set.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ml.config import FEATURE_COLUMNS, RAW_FEATURES

_PASSTHROUGH = [
    "semi_major_axis_au",
    "eccentricity",
    "inclination_deg",
    "perihelion_distance_au",
    "aphelion_distance_au",
]
_ANGLES = {
    "ascending_node": "ascending_node_deg",
    "argument_of_perihelion": "argument_of_perihelion_deg",
}


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    """Map raw SBDB orbital elements to the model input columns (``FEATURE_COLUMNS``)."""
    missing = [c for c in RAW_FEATURES if c not in raw.columns]
    if missing:
        raise ValueError(f"missing input columns: {missing}")
    out = pd.DataFrame(index=raw.index)
    for column in _PASSTHROUGH:
        out[column] = raw[column].astype(float)
    for prefix, column in _ANGLES.items():
        radians = np.deg2rad(raw[column].astype(float))
        out[f"{prefix}_sin"] = np.sin(radians)
        out[f"{prefix}_cos"] = np.cos(radians)
    return out[FEATURE_COLUMNS]

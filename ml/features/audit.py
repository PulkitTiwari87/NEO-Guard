"""Leakage audit of every candidate column (source of truth for docs/DATA_LEAKAGE.md).

Status values: feature | target | identifier | split_only | excluded.
A test asserts that every NEORecord column is audited and that only audited ``feature``
columns are used by the model, so a new column cannot reach training unreviewed.
"""
from __future__ import annotations

FEATURE_AUDIT: dict[str, tuple[str, str]] = {
    "spkid": ("identifier", "Object key. Not a physical property."),
    "designation": ("identifier", "Object key."),
    "full_name": ("identifier", "Label."),
    "name": ("identifier", "Label; null for ~99.6% of objects."),
    "is_potentially_hazardous": ("target", "JPL PHA flag (Y/N)."),
    "absolute_magnitude_h": (
        "excluded",
        "Half of the PHA definition (H <= 22.0). Using it lets a model re-derive the label.",
    ),
    "earth_moid_au": (
        "excluded",
        "Other half of the PHA definition (Earth MOID <= 0.05 au). Derived-target leakage.",
    ),
    "diameter_km": (
        "excluded",
        "Measured for ~2.9% of objects only, and a direct proxy for H (size). Missingness "
        "itself encodes brightness/size, i.e. the H half of the PHA rule.",
    ),
    "albedo": ("excluded", "Only available with a measured diameter (~2.8%); proxy for size."),
    "eccentricity": ("feature", "Keplerian orbital element, available for any orbit solution."),
    "semi_major_axis_au": ("feature", "Keplerian orbital element."),
    "perihelion_distance_au": ("feature", "q = a(1-e); SBDB-published orbital element."),
    "aphelion_distance_au": ("feature", "Q = a(1+e); SBDB-published orbital element."),
    "inclination_deg": ("feature", "Keplerian orbital element."),
    "ascending_node_deg": ("feature", "Keplerian angle; encoded as sin/cos in features."),
    "argument_of_perihelion_deg": ("feature", "Keplerian angle; encoded as sin/cos in features."),
    "mean_anomaly_deg": (
        "excluded",
        "Position along the orbit at the osculation epoch; does not affect MOID or H.",
    ),
    "mean_motion_deg_per_day": ("excluded", "Deterministic function of a (redundant)."),
    "orbital_period_days": ("excluded", "Deterministic function of a (redundant)."),
    "epoch_jd": ("excluded", "Orbit-fit bookkeeping (osculation epoch), not a property."),
    "orbit_class": (
        "excluded",
        "Deterministic function of (a, q, Q) already in the feature set (redundant).",
    ),
    "condition_code": (
        "excluded",
        "Orbit-uncertainty score. Reflects observation effort; PHAs get extra follow-up, so "
        "this is post-outcome information.",
    ),
    "n_obs_used": ("excluded", "Observation count; inflated by PHA follow-up (post-outcome)."),
    "data_arc_days": ("excluded", "Observation span; inflated by PHA follow-up (post-outcome)."),
    "rms": ("excluded", "Orbit-fit residual; observation-process metadata."),
    "last_obs_date": ("excluded", "Follow-up recency; post-outcome information."),
    "first_obs_date": ("split_only", "Used only to build the chronological split."),
    "first_obs_year": ("split_only", "Used only to build the chronological split."),
}


def audited_features() -> set[str]:
    return {c for c, (status, _) in FEATURE_AUDIT.items() if status == "feature"}

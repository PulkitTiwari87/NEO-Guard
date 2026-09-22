"""Internal (application) schema for NEO and close-approach records.

The source schemas (SBDB / CAD field names and string encodings) are mapped to these models
in one place, so the rest of the system never depends on JPL's field names. Constraints are
applied only where they are physically or definitionally valid; see docs/DATA_DICTIONARY.md.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Consistency tolerance for q = a(1-e) and Q = a(1+e). Source values are decimal strings with
# ~8 significant digits; observed worst-case relative error in real data is ~1e-7.
REL_TOL = 1e-4

_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
_CAD_TIME = re.compile(r"^(\d{4})-([A-Za-z]{3})-(\d{2}) (\d{2}):(\d{2})$")

# SBDB source field -> internal field.
SBDB_TO_INTERNAL = {
    "spkid": "spkid",
    "pdes": "designation",
    "full_name": "full_name",
    "name": "name",
    "pha": "is_potentially_hazardous",
    "H": "absolute_magnitude_h",
    "diameter": "diameter_km",
    "albedo": "albedo",
    "e": "eccentricity",
    "a": "semi_major_axis_au",
    "q": "perihelion_distance_au",
    "ad": "aphelion_distance_au",
    "i": "inclination_deg",
    "om": "ascending_node_deg",
    "w": "argument_of_perihelion_deg",
    "ma": "mean_anomaly_deg",
    "n": "mean_motion_deg_per_day",
    "per": "orbital_period_days",
    "moid": "earth_moid_au",
    "epoch": "epoch_jd",
    "condition_code": "condition_code",
    "first_obs": "first_obs_date",
    "last_obs": "last_obs_date",
    "n_obs_used": "n_obs_used",
    "data_arc": "data_arc_days",
    "rms": "rms",
    "class": "orbit_class",
}

CAD_TO_INTERNAL = {
    "des": "designation",
    "orbit_id": "orbit_id",
    "jd": "approach_jd",
    "cd": "approach_time_tdb",
    "dist": "distance_au",
    "dist_min": "distance_min_au",
    "dist_max": "distance_max_au",
    "v_rel": "v_rel_km_s",
    "v_inf": "v_inf_km_s",
    "t_sigma_f": "time_uncertainty",
    "h": "absolute_magnitude_h",
}


class NEORecord(BaseModel):
    """One near-Earth asteroid from SBDB (units: au, degrees, km, days, JD)."""

    model_config = ConfigDict(extra="forbid")

    spkid: int = Field(gt=0)
    designation: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    name: str | None = None
    is_potentially_hazardous: bool | None = None  # JPL flag; null when MOID is unavailable
    absolute_magnitude_h: float | None = None
    diameter_km: float | None = Field(default=None, gt=0)
    albedo: float | None = Field(default=None, ge=0)
    eccentricity: float = Field(ge=0)
    semi_major_axis_au: float = Field(gt=0)
    perihelion_distance_au: float = Field(gt=0, le=1.3)  # NEO definition: q < 1.3 au
    aphelion_distance_au: float = Field(gt=0)
    inclination_deg: float = Field(ge=0, le=180)
    ascending_node_deg: float = Field(ge=0, le=360)
    argument_of_perihelion_deg: float = Field(ge=0, le=360)
    mean_anomaly_deg: float = Field(ge=0, le=360)
    mean_motion_deg_per_day: float = Field(gt=0)
    orbital_period_days: float = Field(gt=0)
    earth_moid_au: float | None = Field(default=None, ge=0)
    epoch_jd: float = Field(gt=0)
    condition_code: str | None = None
    first_obs_date: str
    last_obs_date: str
    first_obs_year: int  # derived from first_obs_date; used only for the chronological split
    n_obs_used: int = Field(ge=0)
    data_arc_days: int | None = Field(default=None, ge=0)
    rms: float = Field(ge=0)
    orbit_class: str = Field(min_length=1)

    @field_validator("name", "condition_code", mode="before")
    @classmethod
    def _blank_to_none(cls, v: Any) -> Any:
        return None if v is None or (isinstance(v, str) and not v.strip()) else v

    @field_validator("is_potentially_hazardous", mode="before")
    @classmethod
    def _yn(cls, v: Any) -> Any:
        if v is None or v is True or v is False:
            return v
        if v in ("Y", "N"):
            return v == "Y"
        raise ValueError("expected 'Y', 'N' or null")

    @field_validator("full_name", mode="before")
    @classmethod
    def _strip(cls, v: Any) -> Any:
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="before")
    @classmethod
    def _derive_year(cls, data: Any) -> Any:
        if isinstance(data, dict) and "first_obs_year" not in data:
            match = re.match(r"^(\d{4})", str(data.get("first_obs_date", "")))
            if match:  # source may contain '2008-??-??'; the year is still valid
                data = {**data, "first_obs_year": int(match.group(1))}
        return data

    @model_validator(mode="after")
    def _orbit_consistency(self) -> NEORecord:
        if self.eccentricity >= 1:
            raise ValueError("eccentricity >= 1 (unbound orbit) is out of scope")
        q_expected = self.semi_major_axis_au * (1 - self.eccentricity)
        ad_expected = self.semi_major_axis_au * (1 + self.eccentricity)
        if abs(self.perihelion_distance_au - q_expected) > REL_TOL * self.perihelion_distance_au:
            raise ValueError("perihelion_distance_au inconsistent with a*(1-e)")
        if abs(self.aphelion_distance_au - ad_expected) > REL_TOL * self.aphelion_distance_au:
            raise ValueError("aphelion_distance_au inconsistent with a*(1+e)")
        return self


class CloseApproachRecord(BaseModel):
    """One Earth close approach from CAD (units: au, km/s, JD TDB)."""

    model_config = ConfigDict(extra="forbid")

    designation: str = Field(min_length=1)
    orbit_id: str | None = None
    approach_jd: float = Field(gt=0)
    approach_time_tdb: datetime
    distance_au: float = Field(ge=0)
    distance_min_au: float = Field(ge=0)
    distance_max_au: float = Field(ge=0)
    v_rel_km_s: float = Field(ge=0)
    v_inf_km_s: float | None = Field(default=None, ge=0)
    time_uncertainty: str | None = None
    absolute_magnitude_h: float | None = None
    body: str = "Earth"

    @field_validator("approach_time_tdb", mode="before")
    @classmethod
    def _parse_cad_time(cls, v: Any) -> Any:
        if isinstance(v, str):
            m = _CAD_TIME.match(v)
            if not m or m.group(2) not in _MONTHS:
                raise ValueError(f"unrecognised CAD date format: {v!r}")
            y, mon, d, hh, mm = m.groups()
            return datetime(int(y), _MONTHS[mon], int(d), int(hh), int(mm))
        return v

    @model_validator(mode="after")
    def _distance_bounds(self) -> CloseApproachRecord:
        eps = 1e-12
        if not (self.distance_min_au - eps <= self.distance_au <= self.distance_max_au + eps):
            raise ValueError("distance not within [distance_min, distance_max]")
        return self

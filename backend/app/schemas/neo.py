"""NEO and close-approach schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from app.db.models import CloseApproach, NeoObject
from ml.config import AU_KM


class NeoSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int  # JPL SPK-ID
    name: str | None
    designation: str
    full_name: str
    is_potentially_hazardous: bool | None  # JPL flag; null when the Earth MOID is unavailable
    absolute_magnitude_h: float | None
    diameter_km: float | None  # measured diameter; null for most objects
    orbit_class: str


class NeoList(BaseModel):
    items: list[NeoSummary]
    total: int
    page: int
    per_page: int


class OrbitalData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    eccentricity: float
    semi_major_axis_au: float
    perihelion_distance_au: float
    aphelion_distance_au: float
    inclination_deg: float
    ascending_node_deg: float
    argument_of_perihelion_deg: float
    mean_anomaly_deg: float
    mean_motion_deg_per_day: float
    orbital_period_days: float
    earth_moid_au: float | None
    epoch_jd: float
    condition_code: str | None
    first_obs_date: str
    last_obs_date: str
    n_obs_used: int
    data_arc_days: int | None
    rms: float


class Approach(BaseModel):
    date: datetime  # TDB calendar date/time, timezone-naive
    time_scale: str = "TDB"
    orbiting_body: str
    miss_distance_au: float
    miss_distance_min_au: float  # 3-sigma bounds
    miss_distance_max_au: float
    relative_velocity_km_s: float
    v_inf_km_s: float | None
    time_uncertainty: str | None  # 3-sigma, as published by JPL (e.g. "04:08", "2_02:16")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def miss_distance_km(self) -> float:
        return self.miss_distance_au * AU_KM

    @classmethod
    def from_row(cls, row: CloseApproach) -> Approach:
        return cls(
            date=row.approach_time_tdb, orbiting_body=row.body,
            miss_distance_au=row.distance_au, miss_distance_min_au=row.distance_min_au,
            miss_distance_max_au=row.distance_max_au, relative_velocity_km_s=row.v_rel_km_s,
            v_inf_km_s=row.v_inf_km_s, time_uncertainty=row.time_uncertainty,
        )


class NeoDetail(NeoSummary):
    albedo: float | None
    orbital_data: OrbitalData
    close_approaches: list[Approach]

    @classmethod
    def build(cls, neo: NeoObject, approaches: list[CloseApproach]) -> NeoDetail:
        return cls(
            **NeoSummary.model_validate(neo).model_dump(),
            albedo=neo.albedo,
            orbital_data=OrbitalData.model_validate(neo),
            close_approaches=[Approach.from_row(a) for a in approaches],
        )


class ApproachList(BaseModel):
    neo_id: int
    approaches: list[Approach]

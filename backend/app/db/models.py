"""ORM models. Column names mirror the internal schema in ml/validation/schema.py."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class DataSource(Base):
    """Provenance of one ingested raw snapshot."""

    __tablename__ = "data_sources"
    __table_args__ = (UniqueConstraint("source_name", "checksum", name="uq_data_sources_snapshot"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(512))
    params: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    record_count: Mapped[int | None] = mapped_column(Integer)
    rejected_count: Mapped[int | None] = mapped_column(Integer)
    schema_version: Mapped[str | None] = mapped_column(String(32))  # API version from signature
    dataset_version: Mapped[str | None] = mapped_column(String(128))
    checksum: Mapped[str] = mapped_column(String(64))  # sha256 of the raw response
    created_at: Mapped[datetime] = _now()


class NeoObject(Base):
    """A near-Earth asteroid (JPL SBDB). Primary key is the SPK-ID."""

    __tablename__ = "neo_objects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    designation: Mapped[str] = mapped_column(String(64), unique=True)
    full_name: Mapped[str] = mapped_column(String(128))
    name: Mapped[str | None] = mapped_column(String(128))
    is_potentially_hazardous: Mapped[bool | None] = mapped_column(Boolean)
    absolute_magnitude_h: Mapped[float | None] = mapped_column(Float)
    diameter_km: Mapped[float | None] = mapped_column(Float)
    albedo: Mapped[float | None] = mapped_column(Float)
    eccentricity: Mapped[float] = mapped_column(Float)
    semi_major_axis_au: Mapped[float] = mapped_column(Float)
    perihelion_distance_au: Mapped[float] = mapped_column(Float)
    aphelion_distance_au: Mapped[float] = mapped_column(Float)
    inclination_deg: Mapped[float] = mapped_column(Float)
    ascending_node_deg: Mapped[float] = mapped_column(Float)
    argument_of_perihelion_deg: Mapped[float] = mapped_column(Float)
    mean_anomaly_deg: Mapped[float] = mapped_column(Float)
    mean_motion_deg_per_day: Mapped[float] = mapped_column(Float)
    orbital_period_days: Mapped[float] = mapped_column(Float)
    earth_moid_au: Mapped[float | None] = mapped_column(Float)
    epoch_jd: Mapped[float] = mapped_column(Float)
    condition_code: Mapped[str | None] = mapped_column(String(4))
    first_obs_date: Mapped[str] = mapped_column(String(16))
    last_obs_date: Mapped[str] = mapped_column(String(16))
    first_obs_year: Mapped[int] = mapped_column(Integer)
    n_obs_used: Mapped[int] = mapped_column(Integer)
    data_arc_days: Mapped[int | None] = mapped_column(Integer)
    rms: Mapped[float] = mapped_column(Float)
    orbit_class: Mapped[str] = mapped_column(String(8))
    data_source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    approaches: Mapped[list[CloseApproach]] = relationship(
        back_populates="neo", cascade="all, delete-orphan", passive_deletes=True
    )


class CloseApproach(Base):
    """One predicted Earth close approach (JPL CAD). Times are TDB, distances in au."""

    __tablename__ = "close_approaches"
    __table_args__ = (
        UniqueConstraint("neo_id", "body", "approach_jd", name="uq_close_approach"),
        Index("ix_close_approaches_time", "approach_time_tdb"),  # window replace + per-year counts
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    neo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("neo_objects.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(String(16))
    orbit_id: Mapped[str | None] = mapped_column(String(16))
    approach_jd: Mapped[float] = mapped_column(Float)
    approach_time_tdb: Mapped[datetime] = mapped_column(DateTime)  # naive: TDB, not UTC
    distance_au: Mapped[float] = mapped_column(Float)
    distance_min_au: Mapped[float] = mapped_column(Float)
    distance_max_au: Mapped[float] = mapped_column(Float)
    v_rel_km_s: Mapped[float] = mapped_column(Float)
    v_inf_km_s: Mapped[float | None] = mapped_column(Float)
    time_uncertainty: Mapped[str | None] = mapped_column(String(16))
    absolute_magnitude_h: Mapped[float | None] = mapped_column(Float)
    data_source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))
    created_at: Mapped[datetime] = _now()

    neo: Mapped[NeoObject] = relationship(back_populates="approaches")


class Model(Base):
    """Model registry (synced from ml/artifacts). ``status`` is managed here, not in files."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    algorithm: Mapped[str] = mapped_column(String(64))
    artifact_path: Mapped[str] = mapped_column(String(256))  # relative to MODEL_DIR; never exposed
    dataset_version: Mapped[str] = mapped_column(String(128))
    feature_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="experimental")
    threshold: Mapped[float] = mapped_column(Float)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    features: Mapped[list[str] | None] = mapped_column(JSONType)
    split: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # training time
    registered_at: Mapped[datetime] = _now()


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(128), unique=True)
    model_version: Mapped[str | None] = mapped_column(ForeignKey("models.version"))
    dataset_version: Mapped[str | None] = mapped_column(String(128))
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Prediction(Base):
    """Prediction made for a known NEO (only stored when the request names ``neo_id``)."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    neo_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("neo_objects.id", ondelete="CASCADE"), index=True
    )
    model_version: Mapped[str] = mapped_column(ForeignKey("models.version"))
    prediction: Mapped[int] = mapped_column(Integer)
    probability: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSONType)
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = _now()

"""Modèle de données : Indice, Source, Import, Observation."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import SEASONS
from app.db import Base


class ClimateIndex(Base):
    """Un indice climatique (ex. RONI). Une ligne par indice."""

    __tablename__ = "climate_index"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)  # "RONI"
    name: Mapped[str] = mapped_column(String(128))
    unit: Mapped[str] = mapped_column(String(16))  # "°C"

    sources: Mapped[list["Source"]] = relationship(back_populates="climate_index")
    observations: Mapped[list["Observation"]] = relationship(back_populates="climate_index")


class Source(Base):
    """D'où viennent les données : fournisseur + URL du fichier."""

    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)
    climate_index_id: Mapped[int] = mapped_column(ForeignKey("climate_index.id"))
    provider: Mapped[str] = mapped_column(String(128))  # "NOAA Climate Prediction Center"
    url: Mapped[str] = mapped_column(String(512), unique=True)

    climate_index: Mapped[ClimateIndex] = relationship(back_populates="sources")
    import_runs: Mapped[list["ImportRun"]] = relationship(back_populates="source")


class ImportRun(Base):
    """Une exécution de l'ETL : quand, quel fichier, combien de lignes."""

    __tablename__ = "import_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    extracted_on: Mapped[date] = mapped_column(Date)  # date de téléchargement du fichier
    file_sha256: Mapped[str] = mapped_column(String(64))  # empreinte du fichier importé
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rows_read: Mapped[int] = mapped_column(Integer, default=0)
    rows_inserted: Mapped[int] = mapped_column(Integer, default=0)
    rows_updated: Mapped[int] = mapped_column(Integer, default=0)
    rows_unchanged: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped[Source] = relationship(back_populates="import_runs")


class Observation(Base):
    """Une valeur de l'indice pour une saison de 3 mois (ex. RONI, DJF 1998 = 2.13 °C)."""

    __tablename__ = "observation"
    __table_args__ = (
        # Une seule valeur par indice, année et saison : c'est l'anti-doublon.
        UniqueConstraint(
            "climate_index_id",
            "year",
            "season",
            name="uq_observation_climate_index_year_season",
        ),
        CheckConstraint(f"season IN {SEASONS}", name="ck_observation_season"),
        CheckConstraint("value BETWEEN -5 AND 5", name="ck_observation_value_range"),
        CheckConstraint("year BETWEEN 1950 AND 2100", name="ck_observation_year_range"),
        # L'API filtre par période : on indexe la date.
        Index("ix_observation_climate_index_period", "climate_index_id", "period_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    climate_index_id: Mapped[int] = mapped_column(ForeignKey("climate_index.id"))
    season: Mapped[str] = mapped_column(String(3))  # "DJF"
    year: Mapped[int] = mapped_column(Integer)  # année telle que publiée par la NOAA
    # 1er jour du mois central (DJF 1998 -> 1998-01-01)
    period_date: Mapped[date] = mapped_column(Date)
    value: Mapped[Decimal] = mapped_column(Numeric(4, 2))  # anomalie en °C
    last_import_run_id: Mapped[int] = mapped_column(ForeignKey("import_run.id"))  # traçabilité

    climate_index: Mapped[ClimateIndex] = relationship(back_populates="observations")
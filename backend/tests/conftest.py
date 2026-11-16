"""Préparation des tests d'API : une base de test séparée, jamais la base de développement."""
import os
from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import database_url
from app.constants import RONI_INDEX_CODE
from app.db import Base, get_session
from app.main import app
from app.models import ClimateIndex, ImportRun, Observation, Source

TEST_DATABASE_NAME = f"{os.environ['POSTGRES_DB']}_test"

# Valeurs réelles du fichier NOAA RONI.ascii.txt (extraction du 14/11/2026), année 1997.
RONI_1997 = [
    ("DJF", 1, "-0.21"), ("JFM", 2, "-0.03"), ("FMA", 3, "0.17"), ("MAM", 4, "0.47"),
    ("AMJ", 5, "0.83"), ("MJJ", 6, "1.20"), ("JJA", 7, "1.50"), ("JAS", 8, "1.84"),
    ("ASO", 9, "2.07"), ("SON", 10, "2.22"), ("OND", 11, "2.25"), ("NDJ", 12, "2.28"),
]


def create_test_database_if_missing() -> None:
    """Crée la base enso_test si elle n'existe pas (connexion à la base système "postgres")."""
    admin_engine = create_engine(database_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DATABASE_NAME}
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory() -> Iterator[sessionmaker[Session]]:
    """Base de test vide, recréée à chaque lancement de pytest, remplie avec l'année 1997."""
    create_test_database_if_missing()
    test_engine = create_engine(database_url(TEST_DATABASE_NAME))
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)

    with session_factory() as session, session.begin():
        climate_index = ClimateIndex(
            code=RONI_INDEX_CODE, name="Relative Oceanic Niño Index", unit="°C"
        )
        source = Source(
            climate_index=climate_index,
            provider="NOAA Climate Prediction Center",
            url="https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
        )
        import_run = ImportRun(
            source=source, extracted_on=date(2026, 11, 14), file_sha256="0" * 64
        )
        session.add_all([climate_index, source, import_run])
        session.flush()
        session.add_all(
            Observation(
                climate_index_id=climate_index.id,
                season=season,
                year=1997,
                period_date=date(1997, center_month, 1),
                value=Decimal(value),
                last_import_run_id=import_run.id,
            )
            for season, center_month, value in RONI_1997
        )

    yield session_factory
    test_engine.dispose()


@pytest.fixture
def client(test_session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """Client HTTP de test : l'API utilise la base de test à la place de la vraie."""

    def get_test_session() -> Iterator[Session]:
        with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()

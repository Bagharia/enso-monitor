"""Test du chargement en base (etl/load.py) : insertion, idempotence, révision NOAA.

Chaque test travaille dans une transaction de la base de test, annulée à la fin :
rien n'est gardé, ni dans la base de test ni, a fortiori, dans la base de développement.
"""
from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from etl.load import get_or_create_climate_index, get_or_create_source, load_observations
from etl.transform import clean_observations
from app.models import ClimateIndex, Observation, Source

# Valeurs réelles du fichier NOAA RONI (extraction du 14/11/2026), début 1998.
RONI_EARLY_1998 = [("DJF", "1998", "2.13"), ("JFM", "1998", "1.82"), ("FMA", "1998", "1.22")]
TEST_INDEX_CODE = "LOAD_TEST"  # indice à part : ne touche pas aux valeurs RONI de conftest.py


@pytest.fixture
def session(test_session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Session dont tout le contenu est annulé (rollback) à la fin du test."""
    with test_session_factory() as test_session:
        yield test_session
        test_session.rollback()


def prepare(session: Session, rows: list[tuple[str, str, str]]):
    """Transforme les lignes comme l'ETL, puis crée (ou retrouve) l'indice et la source de test."""
    observations, _ = clean_observations(pd.DataFrame(rows, columns=["SEAS", "YR", "ANOM"]))
    climate_index = get_or_create_climate_index(session, TEST_INDEX_CODE, "Indice de test", "°C")
    source = get_or_create_source(session, climate_index, "Test", "https://example.org/test.txt")
    return observations, climate_index, source


def run_import(session: Session, rows: list[tuple[str, str, str]], extracted_on: date):
    """Lance l'étape Load comme le ferait python -m etl, sans valider la transaction."""
    observations, climate_index, source = prepare(session, rows)
    return load_observations(
        session, observations, climate_index, source, extracted_on, file_sha256="0" * 64
    )


def stored_value(session: Session, season: str) -> Observation:
    """Observation de l'indice de test enregistrée pour une saison de 1998."""
    return session.scalar(
        select(Observation)
        .join(ClimateIndex)
        .where(ClimateIndex.code == TEST_INDEX_CODE, Observation.season == season)
    )


def test_second_identical_import_inserts_nothing(session: Session):
    first_run = run_import(session, RONI_EARLY_1998, date(2026, 11, 14))
    second_run = run_import(session, RONI_EARLY_1998, date(2026, 11, 14))

    assert (first_run.rows_inserted, first_run.rows_unchanged) == (3, 0)
    assert (second_run.rows_inserted, second_run.rows_updated, second_run.rows_unchanged) == (
        0, 0, 3,
    )
    stored = session.scalars(
        select(Observation).join(ClimateIndex).where(ClimateIndex.code == TEST_INDEX_CODE)
    ).all()
    assert len(stored) == 3  # aucun doublon


def test_revised_value_is_updated_and_traced(session: Session):
    first_run = run_import(session, RONI_EARLY_1998, date(2026, 11, 14))
    # Simulation d'une révision NOAA (valeur modifiée pour le test) : FMA 1998 1.22 -> 1.30.
    revised_rows = [*RONI_EARLY_1998[:2], ("FMA", "1998", "1.30")]
    second_run = run_import(session, revised_rows, date(2026, 12, 14))

    assert (second_run.rows_inserted, second_run.rows_updated, second_run.rows_unchanged) == (
        0, 1, 2,
    )
    revised = stored_value(session, "FMA")
    assert revised.value == Decimal("1.30")
    assert revised.last_import_run_id == second_run.id  # traçabilité : quel import l'a changée
    assert stored_value(session, "DJF").last_import_run_id == first_run.id
    assert session.scalar(select(Source).where(Source.url == "https://example.org/test.txt"))

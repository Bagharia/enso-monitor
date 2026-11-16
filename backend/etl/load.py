"""L de ETL — Load : écrire les observations dans PostgreSQL, avec traçabilité."""
from datetime import date
from decimal import Decimal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClimateIndex, ImportRun, Observation, Source


def get_or_create_climate_index(session: Session, code: str, name: str, unit: str) -> ClimateIndex:
    """Retourne l'indice s'il existe déjà en base, sinon le crée."""
    climate_index = session.scalar(select(ClimateIndex).where(ClimateIndex.code == code))
    if climate_index is None:
        climate_index = ClimateIndex(code=code, name=name, unit=unit)
        session.add(climate_index)
        session.flush()  # envoie l'INSERT pour obtenir l'id, sans valider la transaction
    return climate_index


def get_or_create_source(
    session: Session, climate_index: ClimateIndex, provider: str, url: str
) -> Source:
    """Retourne la source (identifiée par son URL) si elle existe, sinon la crée."""
    source = session.scalar(select(Source).where(Source.url == url))
    if source is None:
        source = Source(climate_index=climate_index, provider=provider, url=url)
        session.add(source)
        session.flush()
    return source


def load_observations(
    session: Session,
    observations: pd.DataFrame,
    climate_index: ClimateIndex,
    source: Source,
    extracted_on: date,
    file_sha256: str,
) -> ImportRun:
    """Écrit les observations en base et enregistre l'import.

    Nouvelle valeur -> insérée. Valeur révisée par la NOAA -> mise à jour. Identique -> ignorée.
    """
    import_run = ImportRun(
        source=source,
        extracted_on=extracted_on,
        file_sha256=file_sha256,
        rows_read=len(observations),
    )
    session.add(import_run)
    session.flush()

    # Observations déjà en base, chargées en une seule requête
    # sous forme de dictionnaire : {(année, saison): observation}
    existing_observations = {
        (observation.year, observation.season): observation
        for observation in session.scalars(
            select(Observation).where(Observation.climate_index_id == climate_index.id)
        )
    }

    rows_inserted = rows_updated = rows_unchanged = 0
    for row in observations.itertuples(index=False):
        # Decimal et pas float : 2.13 reste exactement 2.13 (pas 2.12999...)
        value = Decimal(str(row.value)).quantize(Decimal("0.01"))
        existing_observation = existing_observations.get((row.year, row.season))

        if existing_observation is None:
            session.add(
                Observation(
                    climate_index_id=climate_index.id,
                    season=row.season,
                    year=row.year,
                    period_date=row.period_date,
                    value=value,
                    last_import_run_id=import_run.id,
                )
            )
            rows_inserted += 1
        elif existing_observation.value != value:
            # Valeur révisée par la NOAA : on la met à jour et on note l'import qui l'a changée
            existing_observation.value = value
            existing_observation.last_import_run_id = import_run.id
            rows_updated += 1
        else:
            rows_unchanged += 1

    import_run.rows_inserted = rows_inserted
    import_run.rows_updated = rows_updated
    import_run.rows_unchanged = rows_unchanged
    return import_run

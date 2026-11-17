"""Requêtes partagées par les routes : l'indice affiché et la source de ses données."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import RONI_INDEX_CODE
from app.models import ClimateIndex, ImportRun, Source
from app.schemas import SourceResponse

NO_DATA_DETAIL = "Aucune donnée RONI en base : lancer d'abord l'import (python -m etl)."


def get_climate_index_or_404(session: Session) -> ClimateIndex:
    """Retourne l'indice RONI, ou répond 404 s'il n'a jamais été importé."""
    climate_index = session.scalar(
        select(ClimateIndex).where(ClimateIndex.code == RONI_INDEX_CODE)
    )
    if climate_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_DATA_DETAIL)
    return climate_index


def get_latest_source_or_404(session: Session, climate_index: ClimateIndex) -> SourceResponse:
    """Retourne la source du dernier import de l'indice (affichée à l'utilisateur), ou 404."""
    latest_import_run = session.scalar(
        select(ImportRun)
        .join(Source)
        .where(Source.climate_index_id == climate_index.id)
        .order_by(ImportRun.id.desc())
        .limit(1)
    )
    if latest_import_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_DATA_DETAIL)
    return SourceResponse(
        provider=latest_import_run.source.provider,
        url=latest_import_run.source.url,
        extracted_on=latest_import_run.extracted_on,
    )

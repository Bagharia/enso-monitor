"""Route GET /api/v1/observations : les valeurs de l'indice sur une période."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import RONI_INDEX_CODE
from app.db import get_session
from app.models import ClimateIndex, ImportRun, Observation, Source
from app.schemas import ObservationListResponse, ObservationResponse, SourceResponse

router = APIRouter(prefix="/observations", tags=["observations"])

NO_DATA_DETAIL = "Aucune donnée RONI en base : lancer d'abord l'import (python -m etl)."


@router.get("", response_model=ObservationListResponse)
def list_observations(
    start: date | None = Query(None, description="Début de période incluse (AAAA-MM-JJ)"),
    end: date | None = Query(None, description="Fin de période incluse (AAAA-MM-JJ)"),
    session: Session = Depends(get_session),
) -> ObservationListResponse:
    """Retourne les observations RONI entre start et end, triées par date, avec unité et source."""
    # Format de date invalide (ex. "bonjour") : FastAPI répond 422 tout seul.
    # Période à l'envers : règle métier vérifiée ici, même code 422.
    if start is not None and end is not None and start > end:
        raise HTTPException(
            status_code=422,  # 422 = requête invalide
            detail="Période invalide : la date de début doit précéder la date de fin.",
        )

    climate_index = session.scalar(
        select(ClimateIndex).where(ClimateIndex.code == RONI_INDEX_CODE)
    )
    if climate_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_DATA_DETAIL)

    # La source affichée est celle du dernier import de cet indice.
    latest_import_run = session.scalar(
        select(ImportRun)
        .join(Source)
        .where(Source.climate_index_id == climate_index.id)
        .order_by(ImportRun.id.desc())
        .limit(1)
    )
    # Indice présent mais jamais importé : même réponse que s'il n'y avait rien en base.
    if latest_import_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_DATA_DETAIL)

    # Requête paramétrée : start et end sont envoyés à PostgreSQL à part, jamais collés
    # dans le texte SQL, ce qui empêche toute injection SQL.
    query = select(Observation).where(Observation.climate_index_id == climate_index.id)
    if start is not None:
        query = query.where(Observation.period_date >= start)
    if end is not None:
        query = query.where(Observation.period_date <= end)
    observations = session.scalars(query.order_by(Observation.period_date)).all()

    return ObservationListResponse(
        index_code=climate_index.code,
        index_name=climate_index.name,
        unit=climate_index.unit,
        source=SourceResponse(
            provider=latest_import_run.source.provider,
            url=latest_import_run.source.url,
            extracted_on=latest_import_run.extracted_on,
        ),
        start=start,
        end=end,
        count=len(observations),
        observations=[
            ObservationResponse(
                season=observation.season,
                year=observation.year,
                period_date=observation.period_date,
                value=float(observation.value),
            )
            for observation in observations
        ],
    )

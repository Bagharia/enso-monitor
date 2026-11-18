"""Route GET /api/v1/observations : les valeurs de l'indice sur une période."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Observation
from app.queries import get_climate_index_or_404, get_latest_import_run_or_404
from app.schemas import ObservationListResponse, ObservationResponse, SourceResponse

router = APIRouter(prefix="/observations", tags=["observations"])


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

    climate_index = get_climate_index_or_404(session)
    latest_import_run = get_latest_import_run_or_404(session, climate_index)

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
        source=SourceResponse.from_import_run(latest_import_run),
        start=start,
        end=end,
        count=len(observations),
        observations=[
            ObservationResponse.from_observation(observation) for observation in observations
        ],
    )

"""Route GET /api/v1/episodes : les épisodes El Niño ou La Niña détectés dans la série."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.episodes import EPISODE_THRESHOLD, MIN_EPISODE_SEASONS, Phase, find_episodes
from app.models import Observation
from app.queries import get_climate_index_or_404, get_latest_source_or_404
from app.schemas import EpisodeListResponse, EpisodeResponse

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("", response_model=EpisodeListResponse)
def list_episodes(
    phase: Phase = Query("el_nino", description="el_nino (>= +0,5 °C) ou la_nina (<= -0,5 °C)"),
    session: Session = Depends(get_session),
) -> EpisodeListResponse:
    """Retourne les épisodes de la phase demandée, du plus ancien au plus récent."""
    # Phase inconnue (ex. "neutre") : FastAPI répond 422 tout seul grâce au type Literal.
    climate_index = get_climate_index_or_404(session)
    source = get_latest_source_or_404(session, climate_index)

    observations = session.scalars(
        select(Observation)
        .where(Observation.climate_index_id == climate_index.id)
        .order_by(Observation.period_date)
    ).all()

    return EpisodeListResponse(
        index_code=climate_index.code,
        unit=climate_index.unit,
        source=source,
        phase=phase,
        threshold=float(EPISODE_THRESHOLD),
        min_duration_seasons=MIN_EPISODE_SEASONS,
        episodes=[
            EpisodeResponse.from_episode(episode)
            for episode in find_episodes(observations, phase)
        ],
    )

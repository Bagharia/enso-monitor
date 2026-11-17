"""Schémas Pydantic : la forme exacte des réponses JSON de l'API."""
from datetime import date
from typing import Self

from pydantic import BaseModel

from app.episodes import Episode, Phase, SeasonalValue


class SourceResponse(BaseModel):
    """D'où viennent les données affichées (exigence du sujet : source visible)."""

    provider: str
    url: str
    extracted_on: date


class ObservationResponse(BaseModel):
    """Une valeur de l'indice pour une saison de 3 mois."""

    season: str
    year: int
    period_date: date
    value: float  # Decimal en base, converti en nombre JSON pour le front

    @classmethod
    def from_observation(cls, observation: SeasonalValue) -> Self:
        return cls(
            season=observation.season,
            year=observation.year,
            period_date=observation.period_date,
            value=float(observation.value),
        )


class ObservationListResponse(BaseModel):
    """Réponse de GET /api/v1/observations."""

    index_code: str
    index_name: str
    unit: str
    source: SourceResponse
    start: date | None
    end: date | None
    count: int
    observations: list[ObservationResponse]


class EpisodeResponse(BaseModel):
    """Un épisode : ses bornes, sa durée, son pic et toutes ses valeurs."""

    phase: Phase
    start: ObservationResponse  # première saison de l'épisode
    end: ObservationResponse  # dernière saison de l'épisode
    peak: ObservationResponse  # saison la plus intense
    duration_seasons: int
    is_ongoing: bool
    observations: list[ObservationResponse]

    @classmethod
    def from_episode(cls, episode: Episode) -> Self:
        return cls(
            phase=episode.phase,
            start=ObservationResponse.from_observation(episode.seasons[0]),
            end=ObservationResponse.from_observation(episode.seasons[-1]),
            peak=ObservationResponse.from_observation(episode.peak),
            duration_seasons=len(episode.seasons),
            is_ongoing=episode.is_ongoing,
            observations=[
                ObservationResponse.from_observation(seasonal_value)
                for seasonal_value in episode.seasons
            ],
        )


class EpisodeListResponse(BaseModel):
    """Réponse de GET /api/v1/episodes : les épisodes et la règle qui les définit."""

    index_code: str
    unit: str
    source: SourceResponse
    phase: Phase
    threshold: float  # seuil en valeur absolue (°C)
    min_duration_seasons: int
    episodes: list[EpisodeResponse]

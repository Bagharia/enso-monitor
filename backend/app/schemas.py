"""Schémas Pydantic : la forme exacte des réponses JSON de l'API."""
from datetime import date
from typing import Self

from pydantic import BaseModel

from app.episodes import Episode, Phase, SeasonalValue
from app.models import ImportRun


class SourceResponse(BaseModel):
    """D'où viennent les données affichées (exigence du sujet : source visible)."""

    provider: str
    url: str
    extracted_on: date

    @classmethod
    def from_import_run(cls, import_run: ImportRun) -> Self:
        return cls(
            provider=import_run.source.provider,
            url=import_run.source.url,
            extracted_on=import_run.extracted_on,
        )


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
            start=ObservationResponse.from_observation(episode.seasonal_values[0]),
            end=ObservationResponse.from_observation(episode.seasonal_values[-1]),
            peak=ObservationResponse.from_observation(episode.peak),
            duration_seasons=len(episode.seasonal_values),
            is_ongoing=episode.is_ongoing,
            observations=[
                ObservationResponse.from_observation(seasonal_value)
                for seasonal_value in episode.seasonal_values
            ],
        )


class EpisodeListResponse(BaseModel):
    """Réponse de GET /api/v1/episodes : les épisodes et la règle qui les définit."""

    index_code: str
    unit: str
    source: SourceResponse
    phase: Phase
    episode_threshold: float  # seuil en valeur absolue (°C)
    min_episode_seasons: int
    episodes: list[EpisodeResponse]

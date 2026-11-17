"""Détection des épisodes El Niño / La Niña selon la règle NOAA.

Règle : au moins 5 saisons consécutives au-delà du seuil (>= +0,5 °C pour El Niño,
<= -0,5 °C pour La Niña). Fonctions pures (aucun accès à la base) : faciles à tester.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal, Protocol

Phase = Literal["el_nino", "la_nina"]

EPISODE_THRESHOLD = Decimal("0.5")  # °C, en valeur absolue
MIN_EPISODE_SEASONS = 5


class SeasonalValue(Protocol):
    """Ce dont la détection a besoin : une saison datée et sa valeur (ex. une Observation)."""

    season: str
    year: int
    period_date: date
    value: Decimal


@dataclass(frozen=True)
class Episode:
    """Une suite de saisons consécutives au-delà du seuil."""

    phase: Phase
    seasons: tuple[SeasonalValue, ...]
    is_ongoing: bool  # True si l'épisode touche la dernière valeur connue : il peut continuer

    @property
    def peak(self) -> SeasonalValue:
        """La saison la plus intense : la plus chaude pour El Niño, la plus froide pour La Niña."""
        if self.phase == "el_nino":
            return max(self.seasons, key=lambda seasonal_value: seasonal_value.value)
        return min(self.seasons, key=lambda seasonal_value: seasonal_value.value)


def is_beyond_threshold(value: Decimal, phase: Phase) -> bool:
    """La valeur est-elle au-delà du seuil de la phase ?"""
    if phase == "el_nino":
        return value >= EPISODE_THRESHOLD
    return value <= -EPISODE_THRESHOLD


def are_consecutive(previous: SeasonalValue, current: SeasonalValue) -> bool:
    """Deux saisons se suivent si leurs mois centraux sont espacés d'un mois exactement."""
    months_between = (current.period_date.year - previous.period_date.year) * 12 + (
        current.period_date.month - previous.period_date.month
    )
    return months_between == 1


def find_episodes(seasonal_values: Sequence[SeasonalValue], phase: Phase) -> list[Episode]:
    """Repère les épisodes d'une phase dans une série triée par date.

    Une saison manquante coupe l'épisode : on ne suppose jamais une valeur absente.
    """
    episodes: list[Episode] = []
    current_run: list[SeasonalValue] = []

    def close_current_run(is_ongoing: bool) -> None:
        if len(current_run) >= MIN_EPISODE_SEASONS:
            episodes.append(Episode(phase, tuple(current_run), is_ongoing))
        current_run.clear()

    for seasonal_value in seasonal_values:
        if current_run and not are_consecutive(current_run[-1], seasonal_value):
            close_current_run(is_ongoing=False)
        if is_beyond_threshold(seasonal_value.value, phase):
            current_run.append(seasonal_value)
        else:
            close_current_run(is_ongoing=False)

    close_current_run(is_ongoing=True)  # la série s'arrête pendant l'épisode
    return episodes

"""Test de la détection des épisodes (app/episodes.py).

Les valeurs ci-dessous sont des valeurs de test choisies pour chaque cas, pas des données NOAA.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.constants import SEASONS
from app.episodes import find_episodes


@dataclass
class SeasonalValueStub:
    """Saison de test (même forme qu'une Observation, sans base de données)."""

    season: str
    year: int
    period_date: date
    value: Decimal


def make_series(values: list[str], start_year: int = 2000) -> list[SeasonalValueStub]:
    """Fabrique des saisons consécutives à partir de DJF start_year."""
    series = []
    for position, value in enumerate(values):
        year = start_year + position // 12
        month = position % 12 + 1
        season = SEASONS[month - 1]
        series.append(SeasonalValueStub(season, year, date(year, month, 1), Decimal(value)))
    return series


def test_detects_episode_of_at_least_five_consecutive_seasons():
    series = make_series(["0.40", "0.50", "0.70", "0.90", "0.80", "0.60", "0.30"])

    episodes = find_episodes(series, "el_nino")

    assert len(episodes) == 1
    assert [value.season for value in episodes[0].seasons] == ["JFM", "FMA", "MAM", "AMJ", "MJJ"]
    assert episodes[0].peak.value == Decimal("0.90")
    assert episodes[0].is_ongoing is False


def test_ignores_run_shorter_than_five_seasons():
    series = make_series(["0.60", "0.70", "0.80", "0.90", "0.40"])

    assert find_episodes(series, "el_nino") == []


def test_missing_season_splits_the_run():
    series = make_series(["0.60", "0.70", "0.80", "0.90", "0.80", "0.70"])
    del series[3]  # la saison AMJ manque : les 5 restantes ne sont plus consécutives

    assert find_episodes(series, "el_nino") == []


def test_episode_reaching_end_of_series_is_ongoing():
    series = make_series(["0.10", "0.60", "0.70", "0.80", "0.90", "1.00"])

    episodes = find_episodes(series, "el_nino")

    assert len(episodes) == 1
    assert episodes[0].is_ongoing is True


def test_la_nina_peak_is_the_lowest_value():
    series = make_series(["-0.60", "-0.90", "-1.40", "-1.10", "-0.70", "0.00"])

    episodes = find_episodes(series, "la_nina")

    assert len(episodes) == 1
    assert episodes[0].peak.value == Decimal("-1.40")

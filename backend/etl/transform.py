"""T de ETL — Transform : valider, dédoublonner et dater les observations.

Fonctions pures (aucun accès à la base) : faciles à tester avec pytest.
"""
from datetime import date

import pandas as pd

from app.constants import SEASONS

# Mois central de chaque saison : DJF -> 1 (janvier), JFM -> 2, ..., NDJ -> 12.
SEASON_CENTER_MONTH = {season: position + 1 for position, season in enumerate(SEASONS)}

# Plages acceptées, identiques aux contraintes CHECK de la base (app/models.py).
MIN_YEAR, MAX_YEAR = 1950, 2100
MIN_VALUE, MAX_VALUE = -5, 5


def clean_observations(raw_rows: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Transforme les lignes brutes NOAA en observations propres.

    Retourne (observations valides, problèmes rencontrés).
    Une ligne invalide est écartée et signalée, jamais corrigée en silence.
    """
    observations = raw_rows.rename(columns={"SEAS": "season", "YR": "year", "ANOM": "value"})
    observations["season"] = observations["season"].str.strip().str.upper()
    # errors="coerce" : un texte non numérique devient NaN au lieu de faire planter le script
    observations["year"] = pd.to_numeric(observations["year"], errors="coerce")
    observations["value"] = pd.to_numeric(observations["value"], errors="coerce")

    issues: list[str] = []

    # 1. Écarter les lignes invalides
    is_valid_season = observations["season"].isin(SEASONS)
    is_valid_year = observations["year"].between(MIN_YEAR, MAX_YEAR)  # NaN -> False
    is_valid_value = observations["value"].between(MIN_VALUE, MAX_VALUE)
    is_valid_row = is_valid_season & is_valid_year & is_valid_value

    for row in raw_rows[~is_valid_row].itertuples(index=False):
        issues.append(f"Ligne invalide ignorée : {row.SEAS} {row.YR} {row.ANOM}")
    observations = observations[is_valid_row].copy()

    # 2. Écarter les doublons (même saison, même année) en gardant la première occurrence
    is_duplicate = observations.duplicated(subset=["year", "season"], keep="first")
    for row in observations[is_duplicate].itertuples(index=False):
        issues.append(f"Doublon ignoré : {row.season} {int(row.year)}")
    observations = observations[~is_duplicate].copy()

    # 3. Normaliser les types et calculer la date du point sur la courbe
    observations["year"] = observations["year"].astype(int)
    observations["value"] = observations["value"].round(2)
    observations["period_date"] = [
        date(year, SEASON_CENTER_MONTH[season], 1)
        for year, season in zip(observations["year"], observations["season"])
    ]
    return observations.reset_index(drop=True), issues

"""T de ETL — Transform : valider, dédoublonner et dater les observations.

Fonctions pures (aucun accès à la base) : faciles à tester avec pytest.
"""
from datetime import date

import pandas as pd

from app.constants import SEASONS

# Mois central de chaque saison : DJF -> 1 (janvier), JFM -> 2, ..., NDJ -> 12.
SEASON_CENTER_MONTH = {season: position + 1 for position, season in enumerate(SEASONS)}

# Formats acceptés, vérifiés sur le texte brut du fichier (avant toute conversion) :
YEAR_FORMAT = r"\d{4}"  # 4 chiffres : refuse "1998.5" au lieu de le tronquer en 1998
VALUE_FORMAT = r"-?\d+(\.\d{1,2})?"  # 2 décimales max, comme Numeric(4, 2) en base

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

    issues: list[str] = []

    # 1. Écarter les lignes invalides : d'abord le format du texte, ensuite les plages
    has_valid_year_format = observations["year"].str.fullmatch(YEAR_FORMAT, na=False)
    has_valid_value_format = observations["value"].str.fullmatch(VALUE_FORMAT, na=False)
    # errors="coerce" : un texte non numérique devient NaN au lieu de faire planter le script
    observations["year"] = pd.to_numeric(observations["year"], errors="coerce")
    observations["value"] = pd.to_numeric(observations["value"], errors="coerce")

    is_valid_season = observations["season"].isin(SEASONS)
    is_valid_year = has_valid_year_format & observations["year"].between(MIN_YEAR, MAX_YEAR)
    is_valid_value = has_valid_value_format & observations["value"].between(MIN_VALUE, MAX_VALUE)
    is_valid_row = is_valid_season & is_valid_year & is_valid_value

    for row in raw_rows[~is_valid_row].itertuples(index=False):
        issues.append(f"Ligne invalide ignorée : {row.SEAS} {row.YR} {row.ANOM}")
    observations = observations[is_valid_row].copy()

    # 2. Doublons identiques (même saison, même année, même valeur) : on en garde un seul
    is_identical_duplicate = observations.duplicated(subset=["year", "season", "value"])
    for row in observations[is_identical_duplicate].itertuples(index=False):
        issues.append(f"Doublon identique ignoré : {row.season} {int(row.year)}")
    observations = observations[~is_identical_duplicate].copy()

    # 3. Valeurs contradictoires (même saison, même année, valeurs différentes) :
    #    impossible de savoir laquelle est juste, donc on écarte la saison entière
    is_conflicting = observations.duplicated(subset=["year", "season"], keep=False)
    conflicting_groups = observations[is_conflicting].groupby(["season", "year"])["value"]
    for (season, year), values in conflicting_groups:
        values_text = " / ".join(f"{value:.2f}" for value in values)
        issues.append(
            f"Valeurs contradictoires, saison écartée : {season} {int(year)} ({values_text})"
        )
    observations = observations[~is_conflicting].copy()

    # 4. Normaliser les types et calculer la date du point sur la courbe
    observations["year"] = observations["year"].astype(int)
    observations["period_date"] = [
        date(year, SEASON_CENTER_MONTH[season], 1)
        for year, season in zip(observations["year"], observations["season"])
    ]
    return observations.reset_index(drop=True), issues

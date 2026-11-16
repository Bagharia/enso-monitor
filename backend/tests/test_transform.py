"""Test de données : transformation des observations NOAA (etl/transform.py)."""
from datetime import date

import pandas as pd

from etl.transform import clean_observations


def make_raw_rows(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    """Fabrique des lignes brutes au même format que le fichier NOAA (tout en texte)."""
    return pd.DataFrame(rows, columns=["SEAS", "YR", "ANOM"])


def test_removes_identical_duplicates_and_invalid_rows():
    raw_rows = make_raw_rows(
        [
            ("DJF", "1998", "2.13"),
            ("DJF", "1998", "2.13"),  # doublon identique
            ("XYZ", "1998", "1.00"),  # saison inconnue
            ("JFM", "abcd", "1.00"),  # année non numérique
            ("JFM", "1998.5", "1.00"),  # année non entière
            ("FMA", "1998", "99"),  # valeur hors plage
            ("MAM", "1998", "2.137"),  # plus de 2 décimales
            ("JFM", "1998", "1.82"),
        ]
    )

    observations, issues = clean_observations(raw_rows)

    assert list(observations["season"]) == ["DJF", "JFM"]
    assert len(issues) == 6


def test_conflicting_values_exclude_the_season():
    raw_rows = make_raw_rows(
        [
            ("FMA", "1998", "1.00"),
            ("FMA", "1998", "1.50"),  # même saison, valeur différente
            ("MAM", "1998", "0.81"),
        ]
    )

    observations, issues = clean_observations(raw_rows)

    assert list(observations["season"]) == ["MAM"]
    assert issues == ["Valeurs contradictoires, saison écartée : FMA 1998 (1.00 / 1.50)"]


def test_period_date_is_center_month_of_season():
    raw_rows = make_raw_rows([("DJF", "1998", "2.13"), ("NDJ", "1997", "2.28")])

    observations, _ = clean_observations(raw_rows)

    # DJF 1998 = déc. 1997 + janv. 1998 + févr. 1998 -> mois central : janvier 1998
    assert observations.loc[0, "period_date"] == date(1998, 1, 1)
    # NDJ 1997 = nov. 1997 + déc. 1997 + janv. 1998 -> mois central : décembre 1997
    assert observations.loc[1, "period_date"] == date(1997, 12, 1)

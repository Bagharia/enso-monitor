"""E de ETL — Extract : lire le fichier NOAA tel quel, sans rien modifier."""
from pathlib import Path

import pandas as pd

# Colonnes du fichier RONI.ascii.txt : saison, année, anomalie.
EXPECTED_COLUMNS = ["SEAS", "YR", "ANOM"]


class InvalidFileError(ValueError):
    """Le fichier ne ressemble pas au format NOAA attendu."""


def read_noaa_file(file_path: Path) -> pd.DataFrame:
    """Lit le fichier texte NOAA (colonnes séparées par des espaces).

    Tout est lu en texte (dtype=str) : la conversion en nombres se fait
    dans transform.py, où les valeurs invalides sont détectées.
    """
    raw_rows = pd.read_csv(file_path, sep=r"\s+", dtype=str)
    if list(raw_rows.columns) != EXPECTED_COLUMNS:
        raise InvalidFileError(
            f"Colonnes attendues {EXPECTED_COLUMNS}, colonnes trouvées {list(raw_rows.columns)}"
        )
    return raw_rows

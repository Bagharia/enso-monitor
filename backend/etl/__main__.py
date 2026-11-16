"""Lance l'ETL complet : python -m etl --extracted-on AAAA-MM-JJ"""
import argparse
import hashlib
from datetime import date
from pathlib import Path

from app.constants import RONI_INDEX_CODE
from app.db import SessionLocal
from etl.extract import read_noaa_file
from etl.load import get_or_create_climate_index, get_or_create_source, load_observations
from etl.transform import clean_observations

RONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
DEFAULT_FILE_PATH = Path("data/raw/RONI.ascii.txt")


def main() -> None:
    parser = argparse.ArgumentParser(description="Importe la série NOAA RONI dans PostgreSQL.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE_PATH)
    parser.add_argument("--url", default=RONI_URL, help="URL d'origine du fichier (traçabilité)")
    parser.add_argument(
        "--extracted-on", type=date.fromisoformat, required=True, help="Date de téléchargement"
    )
    args = parser.parse_args()

    # Empreinte SHA-256 : prouve quel fichier exact a été importé
    file_sha256 = hashlib.sha256(args.file.read_bytes()).hexdigest()

    raw_rows = read_noaa_file(args.file)  # Extract
    observations, issues = clean_observations(raw_rows)  # Transform
    for issue in issues:
        print(f"[ATTENTION] {issue}")

    # Load — session.begin() : tout est validé ensemble, ou rien en cas d'erreur
    with SessionLocal() as session, session.begin():
        climate_index = get_or_create_climate_index(
            session, code=RONI_INDEX_CODE, name="Relative Oceanic Niño Index", unit="°C"
        )
        source = get_or_create_source(
            session, climate_index, provider="NOAA Climate Prediction Center", url=args.url
        )
        import_run = load_observations(
            session, observations, climate_index, source, args.extracted_on, file_sha256
        )

    print(
        f"Import n°{import_run.id} terminé : {import_run.rows_read} lues, "
        f"{import_run.rows_inserted} insérées, {import_run.rows_updated} mises à jour, "
        f"{import_run.rows_unchanged} inchangées."
    )


if __name__ == "__main__":
    main()

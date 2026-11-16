"""Configuration lue depuis les variables d'environnement (fichier .env à la racine)."""
import os

from dotenv import find_dotenv, load_dotenv

# Cherche le .env en remontant les dossiers (il est à la racine du projet).
load_dotenv(find_dotenv())


def database_url() -> str:
    """Construit l'URL de connexion PostgreSQL à partir des variables POSTGRES_*."""
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_DB"]
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
"""Configuration lue depuis les variables d'environnement (fichier .env à la racine)."""
import os

from dotenv import find_dotenv, load_dotenv

# Cherche le .env en remontant les dossiers (il est à la racine du projet).
load_dotenv(find_dotenv())


def database_url(database_name: str | None = None) -> str:
    """Construit l'URL de connexion PostgreSQL à partir des variables POSTGRES_*.

    database_name permet de viser une autre base (ex. la base de test) avec les mêmes accès.
    """
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database_name = database_name or os.environ["POSTGRES_DB"]
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database_name}"


def cors_allowed_origins() -> list[str]:
    """Adresses du front autorisées à appeler l'API (séparées par des virgules dans le .env)."""
    return os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")

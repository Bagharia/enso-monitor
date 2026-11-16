"""Connexion à la base : moteur SQLAlchemy et fabrique de sessions."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import database_url


class Base(DeclarativeBase):
    """Classe mère de tous les modèles (tables)."""


engine = create_engine(database_url())
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Fournit une session à une route FastAPI, puis la ferme après la réponse."""
    with SessionLocal() as session:
        yield session

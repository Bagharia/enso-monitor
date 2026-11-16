"""Connexion à la base : moteur SQLAlchemy et fabrique de sessions."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import database_url


class Base(DeclarativeBase):
    """Classe mère de tous les modèles (tables)."""


engine = create_engine(database_url())
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
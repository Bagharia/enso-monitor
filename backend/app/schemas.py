"""Schémas Pydantic : la forme exacte des réponses JSON de l'API."""
from datetime import date

from pydantic import BaseModel


class SourceResponse(BaseModel):
    """D'où viennent les données affichées (exigence du sujet : source visible)."""

    provider: str
    url: str
    extracted_on: date


class ObservationResponse(BaseModel):
    """Une valeur de l'indice pour une saison de 3 mois."""

    season: str
    year: int
    period_date: date
    value: float  # Decimal en base, converti en nombre JSON pour le front


class ObservationListResponse(BaseModel):
    """Réponse de GET /api/v1/observations."""

    index_code: str
    index_name: str
    unit: str
    source: SourceResponse
    start: date | None
    end: date | None
    count: int
    observations: list[ObservationResponse]

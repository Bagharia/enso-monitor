"""Test d'API : base de données injoignable -> 503 avec un message clair (app/main.py)."""
from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_session
from app.main import DATABASE_UNAVAILABLE_DETAIL, app


class UnreachableDatabaseSession:
    """Session factice : chaque requête échoue comme si PostgreSQL était arrêté."""

    def scalar(self, *args, **kwargs):
        raise OperationalError("SELECT ...", {}, Exception("connection refused"))

    scalars = scalar


def get_unreachable_session() -> Iterator[UnreachableDatabaseSession]:
    yield UnreachableDatabaseSession()


def test_returns_503_when_database_is_unreachable():
    app.dependency_overrides[get_session] = get_unreachable_session
    try:
        client = TestClient(app)

        observations_response = client.get("/api/v1/observations")
        episodes_response = client.get("/api/v1/episodes")
        health_response = client.get("/api/v1/health")
    finally:
        app.dependency_overrides.clear()

    assert observations_response.status_code == 503
    assert observations_response.json() == {"detail": DATABASE_UNAVAILABLE_DETAIL}
    assert episodes_response.status_code == 503
    # L'API elle-même reste vivante : le contrôle de santé ne dépend pas de la base.
    assert health_response.status_code == 200

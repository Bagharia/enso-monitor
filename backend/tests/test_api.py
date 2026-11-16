"""Test d'API : route GET /api/v1/observations filtrée par période (app/routes/observations.py)."""
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_session
from app.main import app
from app.models import ClimateIndex
from app.routes import observations as observations_route


def test_returns_observations_within_period(client: TestClient):
    period = {"start": "1997-06-01", "end": "1997-09-30"}

    response = client.get("/api/v1/observations", params=period)

    assert response.status_code == 200
    body = response.json()
    assert body["unit"] == "°C"
    assert body["source"]["provider"] == "NOAA Climate Prediction Center"
    assert body["count"] == 4
    assert [observation["season"] for observation in body["observations"]] == [
        "MJJ", "JJA", "JAS", "ASO",
    ]
    assert body["observations"][0] == {
        "season": "MJJ", "year": 1997, "period_date": "1997-06-01", "value": 1.2,
    }


def test_rejects_period_with_end_before_start(client: TestClient):
    period = {"start": "1997-12-01", "end": "1997-01-01"}  # fin avant début

    response = client.get("/api/v1/observations", params=period)

    assert response.status_code == 422
    assert "début doit précéder la date de fin" in response.json()["detail"]


def test_rejects_invalid_date_format(client: TestClient):
    response = client.get("/api/v1/observations", params={"start": "bonjour"})

    assert response.status_code == 422


def test_returns_404_when_index_has_no_import_run(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
):
    # Indice présent en base mais jamais importé. Ajouté avec flush() sans commit, puis annulé :
    # la base de test partagée par les autres tests n'est jamais modifiée.
    with test_session_factory() as session:
        session.add(ClimateIndex(code="NO_IMPORT", name="Indice sans import", unit="°C"))
        session.flush()  # visible par cette session uniquement

        def get_uncommitted_session() -> Iterator[Session]:
            yield session

        app.dependency_overrides[get_session] = get_uncommitted_session
        monkeypatch.setattr(observations_route, "RONI_INDEX_CODE", "NO_IMPORT")

        response = client.get("/api/v1/observations")
        session.rollback()

    assert response.status_code == 404
    assert "lancer d'abord l'import" in response.json()["detail"]

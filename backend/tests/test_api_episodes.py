"""Test d'API : route GET /api/v1/episodes (app/routes/episodes.py)."""
from fastapi.testclient import TestClient


def test_returns_el_nino_episodes(client: TestClient):
    response = client.get("/api/v1/episodes", params={"phase": "el_nino"})

    assert response.status_code == 200
    body = response.json()
    assert body["threshold"] == 0.5
    assert body["min_duration_seasons"] == 5
    # Base de test : année 1997 seulement, au-dessus de +0,5 °C d'AMJ (0.83) à NDJ (2.28).
    [episode] = body["episodes"]
    assert (episode["start"]["season"], episode["end"]["season"]) == ("AMJ", "NDJ")
    assert episode["duration_seasons"] == 8
    assert episode["peak"] == {
        "season": "NDJ", "year": 1997, "period_date": "1997-12-01", "value": 2.28,
    }
    assert episode["is_ongoing"] is True  # NDJ 1997 est la dernière valeur de la base de test


def test_rejects_unknown_phase(client: TestClient):
    response = client.get("/api/v1/episodes", params={"phase": "neutre"})

    assert response.status_code == 422

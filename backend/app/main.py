"""Application FastAPI : point d'entrée de l'API (uvicorn app.main:app)."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.config import cors_allowed_origins
from app.routes import episodes, observations

app = FastAPI(
    title="ENSO Monitor API",
    description="Indice NOAA RONI (El Niño / La Niña) : observations par période et épisodes.",
    version="1.0.0",
)

# Le front (Vite, autre port) n'a le droit d'appeler l'API que depuis les origines listées.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins(),
    allow_methods=["GET"],
    allow_headers=["*"],
)

API_V1_PREFIX = "/api/v1"

DATABASE_UNAVAILABLE_DETAIL = "Base de données indisponible : réessayez dans quelques instants."


@app.exception_handler(OperationalError)
def database_unavailable(request: Request, error: OperationalError) -> JSONResponse:
    """Base arrêtée ou injoignable : 503 avec un message clair, au lieu d'une erreur 500.

    503 = le service est temporairement indisponible ; ce n'est ni une faute du client (4xx)
    ni un bug du code. Le détail technique de l'erreur n'est jamais renvoyé au navigateur.
    """
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": DATABASE_UNAVAILABLE_DETAIL},
    )

app.include_router(observations.router, prefix=API_V1_PREFIX)
app.include_router(episodes.router, prefix=API_V1_PREFIX)


@app.get(f"{API_V1_PREFIX}/health", tags=["health"])
def health() -> dict[str, str]:
    """Vérifie que l'API répond (contrôle de santé Docker), même si la base est arrêtée."""
    return {"status": "ok"}

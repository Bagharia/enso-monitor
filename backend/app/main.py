"""Application FastAPI : point d'entrée de l'API (uvicorn app.main:app)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_allowed_origins
from app.routes import observations

app = FastAPI(
    title="ENSO Monitor API",
    description="Indice NOAA RONI (El Niño / La Niña) : observations filtrées par période.",
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

app.include_router(observations.router, prefix=API_V1_PREFIX)


@app.get(f"{API_V1_PREFIX}/health", tags=["health"])
def health() -> dict[str, str]:
    """Vérifie que l'API répond (utilisé plus tard par Docker)."""
    return {"status": "ok"}

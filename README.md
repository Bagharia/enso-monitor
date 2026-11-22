# ENSO Monitor

Plateforme d'exploration de l'indice NOAA **RONI** (Relative Oceanic Niño Index)
pour suivre les épisodes El Niño / La Niña et comparer deux épisodes historiques.

Projet de rattrapage HETIC — RNCP 36146 (BC02 / BC03).

## Stack
- Frontend : React, TypeScript, Vite, Recharts
- API : Python, FastAPI
- Données : PostgreSQL, SQLAlchemy, Alembic
- ETL : Python, Pandas

## Lancement avec Docker (tout en une commande)
```bash
cp .env.example .env                          # puis changer POSTGRES_PASSWORD
docker compose up -d --build                  # base + API (migrations au démarrage) + front
docker compose run --rm etl                   # import des données NOAA
```
Site sur http://localhost:8080 (port `HTTP_PORT`), documentation de l'API sur
http://localhost:8080/docs. Caddy sert le front et transmet `/api/*`, `/docs` et
`/openapi.json` à l'API : une seule adresse, pas de CORS. Date du fichier NOAA importé :
`ETL_EXTRACTED_ON` dans le `.env`. Seul Caddy est exposé ; l'API et la base restent
sur le réseau interne de Docker (la base est aussi ouverte sur `127.0.0.1` pour le dev).
Déploiement sur un VPS (documenté, non réalisé) : [docs/deploiement.md](docs/deploiement.md).

## Lancement local (développement)
```bash
cp .env.example .env
docker compose up -d db                       # PostgreSQL seulement

cd backend
python3.12 -m venv .venv                      # première fois seulement
source .venv/bin/activate
pip install -r requirements.txt               # première fois seulement
alembic upgrade head                          # crée / met à jour les tables
python -m etl --extracted-on 2026-11-14       # importe data/raw/RONI.ascii.txt
uvicorn app.main:app --reload                 # API sur http://localhost:8000
```

Documentation interactive de l'API (OpenAPI) : http://localhost:8000/docs

Routes :
- `GET /api/v1/observations?start=1997-11-01&end=1998-02-28` : valeurs sur une période
  (422 si une date est invalide ou si la fin précède le début) ;
- `GET /api/v1/episodes?phase=el_nino` (ou `la_nina`) : épisodes détectés, au moins
  5 saisons consécutives au-delà de ±0,5 °C (422 si la phase est inconnue) ;
- `GET /api/v1/health` : l'API répond.

Front (dans un second terminal, l'API doit tourner) :
```bash
cd web
npm ci                                        # première fois seulement
npm run dev                                   # http://localhost:5173
```
L'adresse de l'API est `http://localhost:8000` par défaut (modifiable avec `VITE_API_BASE_URL`).

## Tests
```bash
cd backend && source .venv/bin/activate
pytest -v                                     # données (ETL) + API

cd web
npm test                                      # front (Vitest) : changer la période
npx tsc -b                                    # vérification des types TypeScript
npm run lint                                  # lint (échoue au moindre avertissement)
npm run build                                 # build de production dans web/dist
```
Les tests d'API utilisent une base séparée `enso_test`, créée et remplie automatiquement
(année 1997 du fichier NOAA) : la base de développement n'est jamais modifiée.

## Usage de l'IA
_À compléter au fil du projet._
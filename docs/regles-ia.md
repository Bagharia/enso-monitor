# ENSO Monitor — instructions pour Claude

## Contexte
Projet de **rattrapage HETIC** (RNCP 36146, blocs BC02 et BC03), **individuel**, réalisé par Alexis.
Application web qui affiche l'indice NOAA **RONI** (El Niño / La Niña) et compare deux épisodes historiques.
- Rendu : dimanche 22/11/2026 (ZIP + dossier de conception PDF de 15 pages max).
- Soutenance : 25-26/11/2026. **La code review à l'oral compte plus que le nombre de fonctionnalités.**
- L'IA est autorisée, mais Alexis doit pouvoir **expliquer et modifier chaque ligne**.

## Règles pour Claude
1. **Expliquer avant de coder.** Pour chaque changement non trivial : le besoin, les alternatives, le choix, ses limites. Langage simple, en français.
2. **Rester dans le périmètre du backlog** (ci-dessous). Ne pas ajouter de fonctionnalité, de dépendance ou d'abstraction non demandée. Sobre et maîtrisé > riche et fragile.
3. **Ne jamais commit ni push.** C'est Alexis qui commit : l'historique Git doit montrer *sa* progression. Proposer le message de commit.
4. **Ne jamais inventer de données ni de résultats.** Pas de valeur climatique fictive, pas de test présenté comme passé s'il n'a pas été exécuté.
5. **Ne jamais modifier une migration Alembic déjà commitée.** Tant qu'elle est locale et la base vide, on peut la régénérer. Sinon, créer une nouvelle migration. L'autogenerate ne détecte pas les renommages : les écrire à la main (`op.alter_column(..., new_column_name=...)`).
6. **Lancer les tests après chaque modification** et montrer le résultat réel.
7. Signaler tout ce qui relève de l'IA pour la section « Usage de l'IA » du README.
8. **`CLAUDE.md` ne doit JAMAIS être commité ni poussé.** Il est ignoré par Git (`.gitignore`) : ne jamais le retirer du `.gitignore`, ne jamais l'inclure dans un `git add` ni dans une proposition de commit.

## Conventions de code
- Code (variables, fonctions, tables, colonnes) **en anglais** ; commentaires, docstrings et messages **en français**.
- Noms explicites, pas d'abréviation obscure : `observations` et pas `df`, `import_run` et pas `run`.
- Clé étrangère : `<table_visée>_id` (ex. `climate_index_id` → `climate_index`, `last_import_run_id` → `import_run`).
- Booléen : préfixe `is_` (`is_valid_row`, `is_duplicate`). Compteur : préfixe `rows_` (`rows_inserted`).
- Contraintes SQL nommées : `uq_<table>_...`, `ck_<table>_...`, `ix_<table>_...`.
- Fichiers ETL nommés par étape : `extract.py`, `transform.py`, `load.py`.
- Constantes en MAJUSCULES ; tuple pour une valeur fixe (`SEASONS`).
- Noms de tests en anglais (c'est du code) ; types TypeScript nommés comme les schémas Pydantic qu'ils copient (*Response).
- Lignes ≤ 100 caractères. Requêtes SQL toujours paramétrées (jamais de f-string avec une donnée utilisateur).
- Commits : `type(scope): description in English` — types `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `data`. (Les deux premiers commits sont en français : convention changée ensuite, historique non réécrit.)

## Stack (imposée par le sujet)
- Frontend : React + TypeScript + Vite, Recharts, tests Vitest + Testing Library
- API : FastAPI + Pydantic, routes sous `/api/v1`
- Données : PostgreSQL 17 (Docker), SQLAlchemy 2, Alembic
- ETL : Python 3.12 + Pandas
- Déploiement : documenté seulement (VPS + Docker Compose + Caddy), pas de mise en ligne réelle

## Structure
```
backend/
  app/          constants.py, config.py (lit le .env), db.py, models.py,
                schemas.py (Pydantic), main.py (FastAPI),
                queries.py (indice + dernier import, 404 ; renvoie des modèles, jamais des schémas),
                episodes.py (détection des épisodes, fonctions pures),
                routes/observations.py, routes/episodes.py
  etl/          extract.py, transform.py, load.py, __main__.py
  alembic/      migrations
  data/raw/     RONI.ascii.txt (source NOAA brute) + SOURCE.md
  tests/        pytest (conftest.py : base de test séparée enso_test) : test_transform,
                test_api, test_episodes, test_api_episodes
web/            React + TypeScript (Vite), tests Vitest
  src/          main.tsx, App.tsx, App.test.tsx (test front), types.ts, format.ts, index.css,
                episodeComparison.ts (+ .test.ts) : texte de comparaison, fonctions pures,
                chartAxis.ts (+ .test.ts) : graduations communes aux deux courbes
  src/api/      client.ts (seul fetch du front), observations.ts, episodes.ts
  src/hooks/    useObservations.ts, useEpisodes.ts (chargement, erreur, annulation)
  src/components/ PeriodFilter, ObservationChart, ObservationTable, SourceNote,
                EpisodeComparison
  src/test/     setup.ts (jest-dom, ResizeObserver simulé)
docs/           dossier de conception, diagrammes
compose.yaml    db (PostgreSQL), api, etl (profil tools, à la demande), web (Caddy)
backend/Dockerfile, backend/.dockerignore   image API + ETL (utilisateur appuser)
web/Dockerfile, web/.dockerignore, web/Caddyfile   build Vite puis Caddy (front + /api/*)
docs/deploiement.md   déploiement VPS documenté (non réalisé), sauvegarde / restauration
```

## Commandes
```bash
docker compose up -d --build                  # Docker : db + api + web -> http://localhost:8080
docker compose run --rm etl                   # Docker : import NOAA (date : ETL_EXTRACTED_ON)
docker compose up -d db                       # dev : PostgreSQL seulement (racine du projet)
cd backend && source .venv/bin/activate
alembic upgrade head                          # crée / met à jour les tables
alembic check                                 # vérifie que modèles et base sont synchronisés
python -m etl --extracted-on 2026-11-14       # importe RONI.ascii.txt
uvicorn app.main:app --reload                 # API -> http://localhost:8000/docs
pytest -v                                     # tests Python

cd web && npm ci                              # dépendances front (première fois)
npm run dev                                   # front -> http://localhost:5173
npm test                                      # test front (Vitest)
npx tsc -b && npm run lint                    # types + lint (oxlint --deny-warnings)
npm run build                                 # build de production
```

## Décisions déjà prises (ne pas remettre en cause sans le dire)
- **Indice RONI** (officiel NOAA depuis le 01/02/2026) plutôt qu'ONI : retire le réchauffement de fond, donc comparaison ancien/récent plus juste.
- **Épisodes comparés : 1997-98 et 2015-16.** Interprétation prudente : l'indice mesure intensité et durée, pas les conséquences.
- Source : `https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt`, extraction du 14/11/2026, format `SEAS YR ANOM`.
- Date d'un point = 1er jour du **mois central** de la saison (DJF 1998 → 1998-01-01, NDJ 1997 → 1997-12-01).
- Import idempotent (upsert) : nouvelle valeur insérée, valeur révisée par la NOAA mise à jour, identique ignorée. Chaque import tracé dans `import_run`.
- Lignes invalides écartées et signalées, jamais corrigées en silence.
- **Épisode** (`app/episodes.py`) : au moins 5 saisons consécutives ≥ +0,5 °C (El Niño) ou ≤ −0,5 °C (La Niña), sur les valeurs RONI à 2 décimales. Une saison manquante coupe l'épisode. Un épisode qui touche la dernière valeur connue est « en cours » (`is_ongoing`). Pic = saison la plus chaude (El Niño) ou la plus froide (La Niña). Conséquence : un réchauffement de moins de 5 saisons n'est pas un épisode (ex. MJJ → ASO 2026, 4 saisons au 14/11/2026).
- Comparaison (US4) : courbes alignées sur la 1re saison de chaque épisode ; pics jugés « comparables » sous 0,1 °C d'écart ; 1997-98 et 2015-16 sélectionnés par défaut (deux El Niño forts à 18 ans d'écart, pas « les plus forts » : 1982-83 a le pic le plus élevé). Axe Y de 0 au pic arrondi au 0,5 supérieur, graduation tous les 0,5 °C.
- Noms : un même concept garde le même nom partout (constante `EPISODE_THRESHOLD` → champ API `episode_threshold`, `MIN_EPISODE_SEASONS` → `min_episode_seasons`) ; côté front, les deux épisodes comparés s'appellent `episodeA` / `episodeB`, comme à l'écran. Conversion modèle → réponse : méthode `from_<modèle>` du schéma (`SourceResponse.from_import_run`, `ObservationResponse.from_observation`, `EpisodeResponse.from_episode`).
- **Docker** : Caddy est la seule porte d'entrée (`/api/*` → API, le reste → front compilé) ; front buildé avec `VITE_API_BASE_URL=""`, donc il appelle `/api/v1` sur sa propre adresse (pas de CORS en Docker ; `CORS_ALLOWED_ORIGINS` sert au dev avec Vite). Caddy transmet aussi `/docs*` et `/openapi.json` (Swagger). Migrations appliquées au démarrage de l'API. ETL = même image que l'API (`enso-monitor-backend`, construite une fois), lancé à la demande (`profiles: ["tools"]`), date d'extraction lue dans `ETL_EXTRACTED_ON` (`.env`). En-têtes de sécurité dont HSTS (sans `includeSubDomains`). `.dockerignore` : jamais de `.env*` dans une image ; `tests/` hors de l'image backend. API sans root (`appuser`). Ports et adresse dans le `.env` : `HTTP_PORT=8080`, `HTTPS_PORT=8443`, `SITE_ADDRESS=:80` (un domaine sur VPS → HTTPS automatique).
- Modèle : `climate_index` 1—N `source` 1—N `import_run` 1—N `observation` ; `climate_index` 1—N `observation`.

## Backlog (MoSCoW)
- **Must** : US1 import NOAA sans doublon et tracé · US2 courbe avec unité et source · US3 filtre de période + erreur claire · US4 comparaison de deux épisodes + limites ✅ (`GET /api/v1/episodes?phase=el_nino|la_nina`, 422 si phase inconnue) · US5 API documentée `GET /api/v1/observations?start=&end=` (422 si invalide) · US6 clavier, responsive, tableau des valeurs
- **Could** : US7 phases colorées (règle des 5 saisons consécutives à ±0,5 °C)
- **Won't** : admin, export, carte ERA5, prévisions

## Tests exigés par le sujet
1. Données : `tests/test_transform.py` (doublons identiques, valeurs contradictoires, lignes invalides, date du mois central) — ✅ fait (3 passed)
2. API : `tests/test_api.py` (route filtrée par période, période à l'envers, date invalide, indice sans import → 404), `tests/test_api_episodes.py` (épisodes, phase inconnue → 422), `tests/test_episodes.py` (règle des épisodes) — ✅ fait (14 passed au total)
3. Front : `web/src/App.test.tsx` (changer la période rappelle l'API et met à jour les valeurs affichées) — ✅ fait ; `web/src/episodeComparison.test.ts` (texte de comparaison), `web/src/chartAxis.test.ts` (graduations de l'axe) — 6 passed au total

Base de test : les tests d'API tournent sur une base séparée `enso_test` (`tests/conftest.py`), jamais sur la base de développement.

## Limites connues
- **`etl/load.py` sans test automatique.** Ce qui se passe : l'upsert (insérée / mise à jour / inchangée) n'est vérifié par aucun test pytest. Pourquoi pas traité : vérifié à la main (import, réimport, révision simulée) ; un test demanderait une base de test dédiée à l'ETL. Détection : les compteurs affichés par `python -m etl` et la table `import_run`.
- **Avertissement `httpx` au lancement de pytest** (« Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead »). Ce qui se passe : Starlette annonce qu'il abandonnera `httpx` pour son `TestClient`. Pourquoi pas traité : les tests passent, rien ne casse aujourd'hui ; changer de dépendance avant le rendu ajoute un risque sans bénéfice. Détection : le « warnings summary » en bas de `pytest -v` ; si une future version de Starlette casse le `TestClient`, les tests d'API échoueront tous à l'import.
- **Base de test créée avec `Base.metadata.create_all` et non avec les migrations Alembic.** Ce qui se passe : les tests d'API valident les modèles Python, pas les fichiers de migration. Pourquoi pas traité : plus simple et plus rapide, et les tables sont identiques tant que modèles et migrations sont synchronisés. Détection : `alembic check` sur la base de dev signale tout écart entre modèles et migrations (« No new upgrade operations detected » = synchronisés).
- **Lignes > 100 caractères dans la migration `ea247baa57dc_schema_initial.py`.** Ce qui se passe : fichier généré par Alembic, 4 lignes trop longues. Pourquoi pas traité : migration déjà commitée, on ne la modifie pas (règle 5). Détection : le contrôle de longueur des lignes la signale.
- **Conteneur `web` (Caddy) en root.** Ce qui se passe : l'image officielle de Caddy tourne en root pour ouvrir les ports 80 et 443 ; l'API et l'ETL tournent en `appuser`. Pourquoi pas traité : garder l'image officielle telle quelle ; l'alternative (utilisateur dédié + capacité `NET_BIND_SERVICE`) ajoute de la configuration. Détection : `docker compose exec web whoami` → `root`.
- **Versions d'images Docker flottantes** (`postgres:17-alpine`, `python:3.12-slim`, `node:24-alpine`, `caddy:2-alpine`). Ce qui se passe : deux builds à des dates différentes peuvent prendre des versions mineures différentes. Pourquoi pas traité : fixer un digest `@sha256:` impose des mises à jour de sécurité manuelles. Détection : `docker compose images` / `docker image inspect` (digest différent d'un build à l'autre).
- **Avertissement « chunk > 500 kB » au `npm run build`.** Ce qui se passe : tout le JavaScript est dans un seul fichier de 594 kB (177 kB compressé), surtout à cause de Recharts. Pourquoi pas traité : une seule page, application locale non mise en ligne ; découper le code (`import()` dynamique) ajouterait de la complexité pour un gain faible. Détection : le message `(!) Some chunks are larger than 500 kB` et la taille de `dist/assets/index-*.js` affichés par `npm run build`.

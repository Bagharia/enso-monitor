# Usage de l'IA

Assistant utilisé : Claude Code (modèle Claude Opus 5.5).
Chaque modification ci-dessous a été relue et validée par Alexis, qui fait lui-même tous les commits.

## Session du 14/11/2026 — structure du projet

- Création à la racine de `.gitignore`, `.env.example`, `compose.yaml` et `README.md`
  (fichiers ensuite retouchés par Alexis : image `postgres:17-alpine`, variables `POSTGRES_*`).
- Déplacement du projet dans `Documents/Code/Projet hetic/enso-monitor/`.

## Session du 16/11/2026 — base de données et migrations

- `backend/alembic/env.py` : branchement de `Base.metadata` (pour l'autogenerate) et de l'URL de
  connexion lue depuis le `.env` (rien en dur dans `alembic.ini`), à partir d'un extrait fourni
  par Alexis.
- Renommage de `app/model.py` en `app/models.py` et de `app/constant.py` en `app/constants.py`,
  pour correspondre aux imports utilisés (`app.models`, `app.constants`).
- Écriture de `app/constants.py` : tuple `SEASONS` des 12 saisons NOAA, relevé dans
  `data/raw/RONI.ascii.txt` (tuple et non liste car injecté dans un `CHECK` SQL).
- Première migration générée (autogenerate), relue puis appliquée.
- Revue du projet face au `CLAUDE.md` : clés étrangères non conformes à la convention
  `<table_visée>_id`, test annoncé comme fait alors qu'absent, une ligne de plus de 100 caractères.
- Correction du nommage dans `app/models.py` : `index_id` → `climate_index_id`
  (tables `source` et `observation`), `last_import_id` → `last_import_run_id`, contrainte
  `uq_observation_climate_index_year_season` et index `ix_observation_climate_index_period`.
- Régénération de la migration initiale (option choisie par Alexis après vérification que
  l'ancienne n'avait jamais été commitée et que la base était vide) : `alembic downgrade base`,
  suppression de l'ancienne migration, nouvelle migration `ea247baa57dc`.
- Après relecture et validation de la migration par Alexis : `alembic upgrade head` (4 tables
  créées, version `ea247baa57dc`), puis `alembic check` → « No new upgrade operations
  detected. » (code de sortie 0).
- `app/models.py` : relation `Source.imports` renommée `Source.import_runs` (et
  `back_populates` mis à jour dans `ImportRun.source`), pour suivre la convention de noms
  explicites. Vérifié avec `configure_mappers()` (les `back_populates` ne sont contrôlés qu'à
  cette étape, pas à l'import) ; `alembic check` toujours sans opération à migrer, car c'est
  une relation Python et non une colonne.
- Décision d'Alexis appliquée : convention de commit passée à l'anglais (règle mise à jour
  dans `CLAUDE.md`). `CLAUDE.md` a d'abord été retiré du `.gitignore` pour être versionné,
  puis Alexis est revenu sur ce choix : il reste local et ignoré par Git (voir plus bas).

## Session du 16/11/2026 — ETL (Extract, Transform, Load)

Code fourni par Alexis, recopié tel quel par l'assistant, qui l'a exécuté et vérifié.

- Étape B : `etl/extract.py`, `etl/transform.py`, `pytest.ini`, `tests/test_transform.py`.
  `pytest -v` → 2 passed. Sur le vrai fichier : 921 observations, 0 problème (921 lignes de
  données comptées aussi avec `awk`, sans pandas).
- Relevé par l'assistant, non corrigé (en attente de décision) : trois cas où `transform.py`
  corrige sans signaler — année non entière tronquée (`1998.5` → 1998), valeur arrondie
  (`2.137` → 2.14), deux valeurs différentes pour la même saison traitées comme un simple
  doublon. Aucun de ces cas n'existe dans le fichier NOAA actuel. Corrigé ensuite (voir plus bas).
- Étape C : `etl/load.py` et `etl/__main__.py`. Vérification préalable : `SessionLocal` créé
  avec `expire_on_commit=False`. Résultats réels :
  - 1er import : 921 insérées ; 2e import identique : 921 inchangées (idempotence) ;
  - révision NOAA simulée sur une copie dans `/tmp` (ASO 2026 : 1.97 → 2.01) : 1 mise à jour,
    puis réimport du vrai fichier : 1 mise à jour, valeur revenue à 1.97 ;
  - empreinte SHA-256 du vrai fichier identique avant et après (fichier non modifié) ;
  - 921 observations en base, `pytest -v` → 2 passed.
- Longueur des lignes vérifiée en caractères (Python) et non en octets (`awk` comptait les
  accents double) : aucune ligne au-delà de 100.
- README : section « Lancement local » complétée (environnement Python, migration, import).

### Correction : trois cas corrigés en silence par `transform.py`

Code fourni par Alexis, recopié tel quel par l'assistant, qui l'a exécuté et vérifié.

- **Avant correction** (3 cas piégés lancés sur l'ancien code) : `1998.5` gardé comme 1998 sans
  message ; `2.137` gardé comme 2.14 sans message ; FMA 1998 à 1.00 et 1.50 signalé comme simple
  « Doublon ignoré », avec 1.00 conservé arbitrairement.
- `etl/transform.py` : format du texte brut vérifié avant conversion (`YEAR_FORMAT` : 4 chiffres,
  `VALUE_FORMAT` : 2 décimales max, comme `Numeric(4, 2)`) ; `.round(2)` supprimé (plus rien à
  arrondir) ; doublons identiques ignorés, valeurs contradictoires → saison entière écartée et
  signalée avec ses valeurs.
- `etl/extract.py` : `EXPECTED_COLUMNS` devient un tuple (convention : tuple pour une valeur fixe).
- `tests/test_transform.py` : 3 tests (cas piégés ajoutés). `pytest -v` → 3 passed.
- **Après correction** : les 3 cas piégés sont écartés et signalés. Vrai fichier NOAA : 921
  observations, 0 problème. Réimport réel (`python -m etl --extracted-on 2026-11-14`) : import
  n°2, 921 lues, 0 insérées, 0 mises à jour, 921 inchangées, même empreinte `1297887f…` : la
  correction ne change aucune donnée réelle.
- Longueur des lignes vérifiée en caractères : maximum 97, aucune au-delà de 100.

### Incident : faux import laissé en base

- **Problème** : la simulation de révision NOAA (copie modifiée dans `/tmp`) a été importée
  dans la base de développement. Elle y a laissé l'import n°3, daté du 14/12/2026 (date
  future) et rattaché à la vraie URL NOAA, car `--url` n'avait pas été précisé : une fausse
  extraction présentée comme venant de la NOAA.
- **Détection** : par Claude Code, en relisant la table `import_run` après les tests.
- **Correction** : base recréée (`alembic downgrade base`, `alembic upgrade head`) puis un
  seul import du vrai fichier → une seule ligne dans `import_run` (921 insérées, empreinte
  SHA-256 `1297887f…` du fichier NOAA).
- **Piste d'amélioration** : tester le chargement sur une base de test séparée, jamais sur la
  base de développement.

### Fichier d'instructions de l'assistant

- `CLAUDE.MD` renommé en `CLAUDE.md` (nom standard) et ignoré par Git : il ne doit jamais être
  commité ni poussé (règle ajoutée dans le fichier lui-même).
- `CLAUDE.md` : règle 5 reformulée (migration *commitée*), statut du test `test_transform.py`
  corrigé en « à faire ».
- `app/models.py` : commentaire de `period_date` déplacé au-dessus de la ligne (limite de
  100 caractères).

## Session du 16/11/2026 — API FastAPI et test d'API

Code fourni par Alexis, recopié tel quel par l'assistant, qui l'a exécuté et vérifié.

- Fichiers : `requirements.txt` (fastapi, uvicorn, httpx), `CORS_ALLOWED_ORIGINS` dans `.env` et
  `.env.example`, `RONI_INDEX_CODE` dans `app/constants.py` (utilisé par `etl/__main__.py`),
  `app/config.py` (`database_url(database_name)`, `cors_allowed_origins()`), `app/db.py`
  (`get_session`), `app/schemas.py`, `app/routes/observations.py`, `app/main.py`,
  `tests/conftest.py`, `tests/test_api.py`.
- Vérifié par l'assistant avant de lancer quoi que ce soit : les 12 valeurs 1997 de
  `conftest.py` et les 4 valeurs attendues (OND 1997 → JFM 1998) sont identiques au fichier
  `data/raw/RONI.ascii.txt`.
- `pytest -v` → 6 passed (3 transform + 3 API). Versions installées : fastapi 0.163.1,
  starlette 1.10.0, uvicorn 0.54.0, httpx 0.28.1.
- Base de dev intacte après les tests : 921 observations, `import_run` toujours à 2 lignes ;
  la base `enso_test` contient les 12 observations de 1997. Cela règle, pour l'API, la piste
  d'amélioration de l'incident ci-dessus (tests sur une base séparée).
- API lancée (`uvicorn app.main:app --reload`) : période 1997-11-01 → 1998-02-28 → 4 valeurs
  (2.25, 2.28, 2.13, 1.82) avec unité et source ; période à l'envers → 422 et message clair ;
  `/api/v1/health` → `{"status":"ok"}` ; `/docs` → 200. CORS : l'origine `localhost:5173` reçoit
  l'en-tête `access-control-allow-origin`, une origine inconnue non.
- Longueur des lignes : aucun fichier de cette étape au-delà de 100 caractères (seule la
  migration Alembic générée et déjà commitée dépasse, non modifiée).
- Signalé par l'assistant : avertissement de Starlette au lancement des tests (`httpx` avec
  `TestClient` déprécié) ; pas bloquant, non traité.

### Corrections après la revue de l'API

Demandées par Alexis après la revue de l'assistant.

- `app/routes/observations.py` : si l'indice existe mais n'a jamais été importé
  (`latest_import_run` vaut `None`), la route renvoie la même 404 que pour un indice absent
  (message commun `NO_DATA_DETAIL`) au lieu de planter en 500. La recherche du dernier import
  est faite juste après celle de l'indice, avant la requête des observations.
- `status.HTTP_422_UNPROCESSABLE_CONTENT` remplacé par `status_code=422` : cette constante
  n'existe que dans les versions récentes de Starlette.
- `tests/conftest.py` : `RONI_INDEX_CODE` au lieu de `"RONI"`.
- `tests/test_api.py` : test de la 404 « indice sans import ». L'indice est ajouté avec
  `flush()` sans `commit()` puis annulé (`rollback()`), et la route reçoit cette session via
  `dependency_overrides` : la base de test partagée n'est jamais modifiée.
- Preuve : sans le correctif, ce test échoue (`AttributeError: 'NoneType' object has no
  attribute 'source'`) ; avec, `pytest -v` → 7 passed. Après les tests, `enso_test` ne contient
  que l'indice RONI et ses 12 observations ; la base de dev est inchangée (921 observations,
  2 lignes dans `import_run`).
- Avertissement `httpx` et `create_all` dans les tests : non traités, notés dans les limites
  connues de `CLAUDE.md`.

## Session du 16/11/2026 — front React

Code fourni par Alexis (archive `web-enso-monitor.zip`), installé et vérifié par l'assistant,
sans modification du code.

- Avant installation : contenu de l'archive listé (28 fichiers, ni `node_modules` ni `dist`),
  `package.json` et `package-lock.json` relus (dépendances du registre npm officiel ; seul
  script d'installation : `fsevents`, standard sur macOS). `web/.gitkeep` supprimé.
- Données du test front vérifiées dans `data/raw/RONI.ascii.txt` : NDJ 1997 = 2.28,
  NDJ 2015 = 2.25.
- `npm ci` : 140 paquets, 0 vulnérabilité. `npm test` → 1 passed ; `npx tsc -b` → aucune
  erreur ; `npx oxlint` (1.94.0) → aucun message (contrôlé sur un fichier volontairement
  fautif : oxlint signale bien les problèmes, mais sort avec le code 0 même en cas
  d'avertissement) ; `npm run build` → built, avertissement « chunk > 500 kB » (594 kB) noté
  dans les limites connues.
- API + front lancés, page rendue dans Chrome sans interface (headless) : courbe affichée,
  résumé « 921 valeurs, maximum +2,40 °C (DJF 1983), minimum -1,95 °C (OND 1988) » (valeurs
  recoupées dans le fichier NOAA), source et date d'extraction visibles ; console sans erreur
  (seulement les messages de Vite et de React en développement).
- Racine `.gitignore` testée seule (dépôt vide temporaire) : exclut bien `web/node_modules`
  et `web/dist` (règles `node_modules/` et `dist/`), en plus de `web/.gitignore`.
- Revue de nommage par l'assistant (rien corrigé sans accord) :
  1. types du front (`Source`, `Observation`, `ObservationList`) nommés autrement que les
     schémas Pydantic qu'ils copient, et en conflit avec les modèles SQLAlchemy ;
  2. même année 1950 nommée `MIN_YEAR` (ETL), `FIRST_YEAR` puis `minYear` (front) ;
  3. noms vagues `item`, `max`, `min` dans les `reduce` de `ObservationChart.tsx` ;
  4. nom du test front en français, tests Python en anglais ;
  5. mineur : paquet npm nommé `web`.
  Défauts visuels relevés sur la capture : libellés des seuils superposés et illisibles,
  axe vertical jusqu'à 6 °C pour un maximum de 2,40 °C. oxlint sort avec le code 0 même
  en cas d'avertissement.

### Front v2 (`web-enso-monitor-v2.zip`) — décisions d'Alexis

Code fourni par Alexis, installé et vérifié par l'assistant, sans modification du code.

- Décisions : types renommés `SourceResponse`, `ObservationResponse`,
  `ObservationListResponse` ; `MIN_YEAR` / `MAX_YEAR` dans `App.tsx` ; `highestSoFar`,
  `lowestSoFar`, `observation` dans les `reduce` ; test renommé en anglais ; paquet
  `enso-monitor-web` ; script `lint` = `oxlint --deny-warnings` ; légende des seuils en HTML
  sous la courbe ; axe vertical symétrique arrondi au demi-degré supérieur.
- Règles ajoutées dans `CLAUDE.md` : noms de tests en anglais (c'est du code) ; types
  TypeScript nommés comme les schémas Pydantic qu'ils copient (*Response).
- Avant remplacement : différences v1 → v2 relues (seul changement du lockfile : le nom du
  paquet). `web/` remplacé en gardant `node_modules`, puis `npm ci` (0 vulnérabilité).
- `npm test` → 1 passed ; `npx tsc -b` → aucune erreur ; `npm run lint` → aucun message,
  code 0 (et code 1 sur un fichier volontairement fautif : `--deny-warnings` fonctionne) ;
  `npm run build` → built, chunk de 594 kB (limite connue).
- Capture headless à 1280 px : légende lisible, axe de -2,5 à +2,5 °C ; console sans erreur.
  Relevé, non corrigé : graduations irrégulières (-2,5 / -0,5 / 1,5 / 2,5, sans 0 ni +0,5),
  écrites avec un point alors que le reste de la page utilise la virgule.
- Mobile : la capture headless à 390 px débordait, mais c'était un effet de la largeur
  minimale de la fenêtre de Chrome. Dans une iframe de 390 px et de 320 px, l'en-tête et le
  filtre tiennent dans la largeur. La courbe n'a pas pu être vérifiée en mobile (les données
  ne se chargent pas dans l'iframe headless, alors que l'API répond 200) : à vérifier à la
  main dans le navigateur.

### Corrections demandées par Alexis avant le commit du front (17/11/2026)

Code écrit par l'assistant, à la demande d'Alexis.

- `web/src/App.tsx` : `MAX_YEAR` renommé `CURRENT_YEAR` (année en cours), pour ne pas le
  confondre avec `MAX_YEAR` de l'ETL (limite de validation 2100). `MIN_YEAR` (1950) inchangé :
  même valeur et même sens des deux côtés.
- `web/src/components/ObservationChart.tsx` : graduations explicites tous les 0,5 °C
  (`AXIS_TICK_STEP`, liste `axisTicks`, `interval={0}` pour qu'aucune ne soit masquée) ;
  0 et les deux seuils sont toujours marqués.
- `web/src/format.ts` : `formatAxisValue` écrit les graduations à la française (« +1,5 »,
  « 0,0 », « -1,5 »), comme le reste de la page.
- Vérifications : `npm test` → 1 passed ; `npx tsc -b` et `npm run lint` sans erreur ;
  `npm run build` → built ; aucune ligne au-delà de 100 caractères. Capture headless à
  1280 px : graduations de -2,5 à +2,5 °C tous les 0,5, alignées avec les lignes des seuils ;
  console sans erreur.

## Session du 17/11/2026 — US4 : comparaison de deux épisodes

Code fourni par Alexis (`backend-episodes.zip`, `web-enso-monitor-v4.zip`), installé et vérifié
par l'assistant. Seule modification de l'assistant : l'adaptation du test 404 (ci-dessous).

- Avant d'écraser : `app/routes/observations.py` comparé avec la version précédente. Aucune
  perte de comportement : recherche de l'indice, 404 « indice sans import », message commun et
  source du dernier import déplacés dans `app/queries.py` ; conversion d'une observation
  déplacée dans `ObservationResponse.from_observation`. Seul le commentaire « indice présent
  mais jamais importé » a disparu (le cas reste décrit par la docstring, plus brièvement).
- `tests/test_api.py` adapté : le `monkeypatch` de `RONI_INDEX_CODE` vise maintenant
  `app.queries` (et plus `app.routes.observations`). Avant adaptation, le test échouait
  (`AttributeError ... has no attribute 'RONI_INDEX_CODE'`). Après : il passe, et il échoue
  toujours si on retire la vérification `None` de `queries.py` (testé puis remis à l'identique).
- `pytest -v` → 14 passed (3 transform, 4 API observations, 2 API épisodes, 5 épisodes).
- API lancée, valeurs recoupées dans `data/raw/RONI.ascii.txt` :
  `/episodes?phase=el_nino` → 22 épisodes, dont AMJ 1997 → MAM 1998 (12 saisons, pic 2.28 en
  NDJ 1997) et FMA 2015 → MAM 2016 (14 saisons, pic 2.25 en NDJ 2015) ; `phase=neutre` → 422 ;
  `phase=la_nina` → 22 épisodes. Le réchauffement de 2026 (MJJ → ASO, 4 saisons ; AMJ à 0.49)
  n'est pas encore un épisode selon la règle.
- Front : `web/` sauvegardé hors projet (non commité), puis remplacé par la v4 en gardant
  `node_modules` ; `npm ci` (0 vulnérabilité). `npm test` → 4 passed ; `npx tsc -b` et
  `npm run lint` sans erreur ; `npm run build` → built (601 kB, limite connue). Aucune ligne
  au-delà de 100 caractères (front et backend).
- La v4 reprend les corrections du 17/11 sous d'autres noms (choix d'Alexis) : `FIRST_YEAR` /
  `LATEST_YEAR` au lieu de `MIN_YEAR` / `CURRENT_YEAR`, `AXIS_STEP`, unité passée par
  `formatAxisValue` ; `interval={0}` retiré (toutes les graduations restent affichées à 1280 px).
- Capture headless à 1280 px : section « Comparer deux épisodes El Niño » affichée (choix A/B,
  tableau, courbes superposées, mesures, limites) ; courbe principale inchangée ; console
  sans erreur.
- Relevé par l'assistant, non corrigé (en attente de décision) : le commentaire
  « les deux El Niño les plus forts » est faux (1982-83 a le pic le plus élevé, +2,40 °C) ;
  l'affirmation sur le « tableau publié par la NOAA » arrondi au dixième n'a pas été vérifiée ;
  incohérences de nommage listées dans la réponse de cette session.

## Session du 18/11/2026 — refactor après la revue de US4

Les 11 points relevés par l'assistant à la session précédente ont été tranchés par Alexis
(textes et noms choisis par lui), puis appliqués et vérifiés par l'assistant.

- Commentaire faux corrigé : les épisodes par défaut sont « deux El Niño forts à 18 ans
  d'écart », choix du projet (1982-83 a le pic le plus élevé).
- Limite affichée : mention du tableau NOAA retirée (affirmation non vérifiée). Le test ne
  vérifiait pas cette phrase : rien à adapter.
- Noms alignés sur les constantes : champs API `episode_threshold` et `min_episode_seasons`
  (back, types front, tests) ; `Episode.seasons` devient `Episode.seasonal_values` ; variable
  de boucle `seasonal_value` dans `test_episodes.py`.
- `app/queries.py` ne renvoie plus que des modèles : `get_latest_import_run_or_404` renvoie un
  `ImportRun`, converti par `SourceResponse.from_import_run` dans `schemas.py`. `queries.py`
  n'importe plus `schemas`. Commentaire « indice présent mais jamais importé » remis.
- Front : `first` / `second` deviennent `episodeA` / `episodeB` (variables, couleurs,
  `dataKey`), comme à l'écran ; `seasonName` devient `seasonAndYear(observation)` ; titre de
  section via `useId` ; constante `THRESHOLD_COLOR`.
- Axe Y de la comparaison : de 0 au plus haut pic arrondi au 0,5 supérieur, graduation tous
  les 0,5 °C (même logique que la courbe principale).
- `App.test.tsx` : retour à `toHaveBeenLastCalledWith` (assertion plus stricte).
- Vérifications : `pytest -v` → 14 passed ; `npm test` → 4 passed ; `npx tsc -b`, `npm run lint`
  sans erreur ; `npm run build` → built ; aucune ligne au-delà de 100 caractères hors migration
  Alembic générée (déjà commitée, non modifiée). `/episodes?phase=el_nino` : mêmes valeurs
  qu'avant (22 épisodes, 1997-98 : 12 saisons, pic 2.28 ; 2015-16 : 14 saisons, pic 2.25).
  Capture headless à 1280 px : graduations de 0,0 à +2,5 °C, le seuil +0,5 °C a la sienne.

## Session du 18/11/2026 — fin de la revue US4, puis Docker

Points restants de la revue, textes et choix d'Alexis, appliqués par l'assistant :
- commentaire de `COMPARABLE_PEAK_GAP` réécrit (plus de référence aux arrondis NOAA, non vérifiée) ;
- calcul de l'axe vertical factorisé dans `web/src/chartAxis.ts` (`AXIS_STEP`,
  `roundUpToAxisStep`, `axisTicks`), utilisé par les deux courbes, avec `chartAxis.test.ts`
  (2 tests). `npm test` → 6 passed ; `tsc`, lint et build sans erreur.

Docker (`docker-step.zip` fourni par Alexis, installé et vérifié par l'assistant) :
- `compose.yaml` comparé avec l'ancien avant remplacement : le service `db` est identique,
  rien n'est perdu ; ajout des services `api`, `etl` (à la demande) et `web` (Caddy).
- `.env` et `.env.example` : ajout de `HTTP_PORT=8080`, `HTTPS_PORT=8443`, `SITE_ADDRESS=:80` ;
  `CORS_ALLOWED_ORIGINS` gardé pour le dev avec Vite.
- `docker compose up -d --build` : `db` et `api` healthy, `web` running.
- `docker compose run --rm etl` : d'abord en échec le 18/11 (`failed to solve:
  DeadlineExceeded` sur `FROM python:3.12-slim` ; `docker pull` bloqué aussi, alors que le
  registre répondait depuis le Mac et depuis un conteneur : téléchargement d'image du démon
  OrbStack bloqué). Repli le 18/11 : ETL lancé dans le conteneur `api` → 921 inchangées.
  Le 19/11, après redémarrage d'OrbStack par Alexis : `docker pull` réussi, puis
  `docker compose run --rm etl` → image `etl` construite, « 921 lues, 0 insérées,
  0 mises à jour, 921 inchangées » (import n°4), utilisateur `appuser`.
- Vérifié par `curl` sur http://localhost:8080 : `/api/v1/health` → `{"status":"ok"}` ;
  `/api/v1/episodes?phase=el_nino` → 22 épisodes, mêmes valeurs qu'en local ; en-têtes
  `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy` présents.
  Aucun `localhost:8000` dans le JavaScript du conteneur `web` (URL de base compilée vide).
  `whoami` : `appuser` dans `api`, mais `root` dans `web` (Caddy). Capture headless : page
  complète, console sans message.
- Relevé par l'assistant, non corrigé : la documentation Swagger (`/docs`, `/openapi.json`)
  n'est pas joignable via Caddy (le front est renvoyé à la place) ; autres incohérences listées
  dans la réponse de cette session.

## Session du 19/11/2026 — revue Docker appliquée

Décisions d'Alexis sur les points relevés par l'assistant, appliquées et vérifiées par l'assistant :
- Caddyfile : `/docs*` et `/openapi.json` transmis à l'API (Swagger de nouveau accessible) ;
  en-tête `Strict-Transport-Security: max-age=31536000` (sans `includeSubDomains`) ; volume
  `caddy_config:/config`.
- `compose.yaml` : image commune `enso-monitor-backend` pour `api` et `etl` (construite une
  fois) ; date d'extraction lue dans `ETL_EXTRACTED_ON` (`.env`, `.env.example`) ;
  commentaires impersonnels.
- `.dockerignore` : `.env*` et `Dockerfile` exclus des deux images, `tests/` de l'image backend.
- Commentaire du Dockerfile backend limité à l'API et à l'ETL ; `web` en root et versions
  d'images flottantes ajoutés aux limites (`docs/deploiement.md`, `CLAUDE.md`).
- `docs/deploiement.md` : sauvegarde et restauration avec les variables du conteneur `db`
  (`-T`, `--clean --if-exists`, `ON_ERROR_STOP=1`) ; ajouts de l'assistant, expliqués dans le
  document.
- Vérifications : `docker compose up -d --build` → `db`, `api` healthy, `web` running ;
  `/api/v1/health` → ok ; `/docs` → Swagger UI affiché (capture headless) ; `/openapi.json` →
  3 routes ; en-têtes `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Strict-Transport-Security`
  présents ; `docker compose run --rm etl` → « 921 lues, 0 insérées, 0 mises à jour,
  921 inchangées » sans reconstruire d'image, en `appuser` ; `tests/` absent de `/app`.
  Sauvegarde puis restauration testées dans une base temporaire (supprimée ensuite) :
  sans erreur, deux fois de suite.

## Session du 22/11/2026 — rendu : commits, dossier, base indisponible

- Préparation des commits du rendu (`git add` explicites, jamais `git add .`) ; vérifié avant
  chaque commit que `CLAUDE.md` et `.env` sont ignorés par Git. Commits lancés par Alexis.
- `docs/regles-ia.md` : copie de `CLAUDE.md`, pour que le jury puisse lire les règles données à
  l'assistant (`CLAUDE.md` reste local et ignoré par Git). Copie resynchronisée en fin de session.
- Contrôle du dossier de conception avant commit : PDF rendu page par page, chiffres recoupés avec
  `RONI.ascii.txt` (durées, pics, 921 valeurs) et avec le code (Caddyfile, contraintes SQL,
  commits cités). Relevé par l'assistant et corrigé par Alexis : une page blanche en fin de PDF
  (15 pages), un renvoi « détail en section 5 » qui ne couvrait qu'une correction sur quatre.
- README réécrit par l'assistant à partir du code et du dossier : fonctionnalités, choix sur les
  données, routes, tests, structure, limites ; la section « Usage de l'IA », restée vide, est
  remplie à partir du bilan du dossier.
- **Base indisponible → 503 + « Réessayer », et tests de `load.py`.** Amélioration identifiée par
  Alexis en comparant avec un autre projet du même sujet ; **aucun code repris** de ce projet.
  Code fourni par Alexis (`ameliorations-503-tests.zip`, écrit sur la version `3b9a67f`) ;
  l'assistant a vérifié qu'aucun des 8 fichiers n'avait changé localement depuis `3b9a67f`
  (pas de conflit), relu chaque modification, puis copié les fichiers.
  - `app/main.py` : `OperationalError` → 503 avec un message en français, sans détail technique.
  - Front : bouton « Réessayer » ; `useObservations` / `useEpisodes` renvoient `{ state, retry }`.
  - Vérifié par l'assistant que `etl/load.py` ne fait que des `flush()` (le `commit()` est dans
    `etl/__main__.py`) : le `rollback()` de `test_load.py` annule donc bien tout.
  - Vérifié que le test 503 **échoue** quand le gestionnaire d'erreur est désactivé, puis passe.
- Vérifications (sorties réelles) : `pytest -v` → 17 passed ; `npm test` → 7 passed ;
  `npx tsc -b` sans erreur ; `npm run lint` code 0 ; `npm run build` OK (avertissement connu,
  JS de 601 kB). Docker : `docker compose up -d --build` → `api` healthy ; `docker compose stop db`
  → `/api/v1/observations` et `/api/v1/episodes` répondent 503 « Base de données indisponible : … »,
  `/api/v1/health` 200 ; `docker compose start db` → 200 avec les valeurs, sans redémarrer l'API.

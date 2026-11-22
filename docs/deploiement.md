# Déploiement d'ENSO Monitor

> Ce déploiement est **documenté, pas réalisé** : le sujet ne demande pas de mise en ligne réelle.
> Tout ce qui suit est vérifiable en local avec la même commande `docker compose`.

## Architecture

```
Navigateur ──HTTPS──▶ Caddy (service web, ports 80/443)
                        ├── /api/*  ──▶ API FastAPI (service api, port 8000, réseau interne)
                        │                 └──▶ PostgreSQL (service db, port 5432, réseau interne)
                        └── le reste ──▶ fichiers statiques du front (React compilé)

ETL (service etl) : lancé à la demande, écrit dans PostgreSQL puis s'arrête.
```

- **Une seule adresse** pour le front et l'API : Caddy transmet `/api/*` à l'API. Le front appelle
  donc `/api/v1/...` sur sa propre adresse, et le navigateur n'a pas besoin de CORS.
- **Seul Caddy est exposé** à Internet. L'API et la base ne sont joignables que par le réseau
  interne de Docker.
- **HTTPS automatique** : avec un nom de domaine dans `SITE_ADDRESS`, Caddy obtient et renouvelle
  seul un certificat Let's Encrypt.

## En local (vérification)

```bash
cp .env.example .env              # puis remplir les valeurs
docker compose up -d --build      # base + API (migrations au démarrage) + front
docker compose run --rm etl       # import des données NOAA (une fois, puis à chaque nouveau fichier)
```

Le site est alors sur http://localhost:8080 (port `HTTP_PORT`, 8080 par défaut).

## Sur un VPS Linux

1. **Serveur** : un VPS Linux avec Docker et le plugin Compose installés.
2. **Nom de domaine** : un enregistrement DNS `A` pointant vers l'adresse IP du VPS.
3. **Pare-feu** : n'ouvrir que les ports 22 (SSH), 80 et 443.
4. **Code** : `git clone` du dépôt sur le serveur.
5. **Configuration** (`.env`, jamais commité) :
   - `POSTGRES_PASSWORD` : un mot de passe long et aléatoire ;
   - `SITE_ADDRESS=enso.mon-domaine.fr` ;
   - `HTTP_PORT=80` et `HTTPS_PORT=443`.
6. **Base non exposée** : dans `compose.yaml`, retirer la section `ports` du service `db`
   (elle ne sert qu'aux outils sur la machine de développement).
7. **Lancement** : `docker compose up -d --build`, puis `docker compose run --rm etl`.

## Exploitation

| Besoin | Commande |
|---|---|
| Voir l'état des services | `docker compose ps` |
| Lire les logs de l'API | `docker compose logs -f api` |
| Mettre à jour le code | `git pull && docker compose up -d --build` |
| Importer un nouveau fichier NOAA | remplacer `backend/data/raw/RONI.ascii.txt`, mettre sa date de téléchargement dans `ETL_EXTRACTED_ON` (`.env`), puis `docker compose run --rm etl` |
| Sauvegarder la base | `docker compose exec -T db sh -c 'pg_dump --clean --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB"' > sauvegarde.sql` |
| Restaurer une sauvegarde | `docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < sauvegarde.sql` |

Les variables `POSTGRES_*` sont celles du conteneur `db` (donc du `.env`) : aucun identifiant
n'est écrit dans la commande. `-T` : pas de terminal, le flux SQL passe tel quel.
`--clean --if-exists` : la sauvegarde supprime puis recrée les tables, donc la restauration
remplace les données existantes au lieu d'échouer sur des doublons.

## Limites connues

- Pas d'intégration continue : les tests se lancent à la main (`pytest`, `npm test`).
- Les migrations s'appliquent au démarrage de l'API : simple pour un seul serveur, à revoir
  si plusieurs instances de l'API démarraient en même temps.
- L'image de l'API installe aussi pytest et httpx (un seul `requirements.txt`), sans les tests
  eux-mêmes (`tests/` exclu par `.dockerignore`) : quelques Mo inutiles en production. Séparer
  les dépendances de test (`requirements-dev.txt`) serait plus propre.
- Le conteneur `web` (Caddy) tourne en root : l'image officielle de Caddy est prévue ainsi,
  car Caddy doit ouvrir les ports 80 et 443 (ports réservés sous Linux). L'API et l'ETL, eux,
  tournent avec l'utilisateur `appuser`. Piste : lancer Caddy avec un utilisateur dédié et la
  capacité `NET_BIND_SERVICE`, non faite pour garder l'image officielle telle quelle.
- Versions d'images flottantes (`postgres:17-alpine`, `python:3.12-slim`, `node:24-alpine`,
  `caddy:2-alpine`) : deux builds à des dates différentes peuvent utiliser des versions
  mineures différentes. Fixer un digest (`@sha256:...`) rendrait le build reproductible, au prix
  de mises à jour de sécurité manuelles.

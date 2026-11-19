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
| Importer un nouveau fichier NOAA | remplacer `backend/data/raw/RONI.ascii.txt`, adapter `--extracted-on`, puis `docker compose run --rm etl` |
| Sauvegarder la base | `docker compose exec db pg_dump -U enso enso > sauvegarde.sql` |

## Limites connues

- Pas d'intégration continue : les tests se lancent à la main (`pytest`, `npm test`).
- Les migrations s'appliquent au démarrage de l'API : simple pour un seul serveur, à revoir
  si plusieurs instances de l'API démarraient en même temps.
- L'image de l'API contient aussi les outils de test (pytest) : quelques Mo de plus, sans risque
  connu, mais une image séparée « production » serait plus propre.

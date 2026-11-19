# Image de l'API et de l'ETL (même code Python, deux commandes différentes).
FROM python:3.12-slim

# Pas de fichiers .pyc, et les logs s'affichent tout de suite.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances d'abord : cette couche reste en cache tant que requirements.txt ne change pas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sécurité : le code ne tourne pas en root dans le conteneur.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Au démarrage : appliquer les migrations, puis lancer l'API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

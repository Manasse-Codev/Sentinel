# Sentinel API

Backend FastAPI asynchrone pour la plateforme Sentinel.

## Démarrage local

```bash
# Installation des dépendances avec uv
uv sync --all-extras

# Lancement du serveur de développement
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Vérification de l'état de santé

```bash
curl http://localhost:8000/api/v1/health
```

## Migrations Alembic

```bash
# Appliquer les migrations
uv run alembic upgrade head
```

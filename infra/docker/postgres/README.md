# PostgreSQL — Sentinel

## Extensions activées

- `uuid-ossp` — génération d'UUID
- `pgcrypto` — fonctions cryptographiques
- `citext` — type texte insensible à la casse (utilisé pour `users.email`)
- `pg_trgm` — recherche floue (utilisée par `search_history` en V1.1)

## Partitionnement

Les tables suivantes sont partitionnées par mois :

- `sensor_readings` (sur `recorded_at`)
- `events` (sur `occurred_at`)
- `audit_logs` (sur `created_at`)

Les partitions sont créées par des migrations Alembic dédiées.

## Connexion

- **Async** (FastAPI) : `postgresql+asyncpg://...`
- **Sync** (Alembic) : `postgresql+psycopg://...`

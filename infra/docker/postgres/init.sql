-- ============================================================
-- Sentinel — Initialisation PostgreSQL
-- Exécuté une seule fois au premier démarrage du conteneur.
-- ============================================================

-- Extensions requises
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Timezone par défaut
SET timezone = 'UTC';

-- Note : le schéma applicatif est géré par Alembic (apps/api/migrations).
-- Ce fichier ne fait qu'activer les extensions et les réglages de base.

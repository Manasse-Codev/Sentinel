# Brief — 01-data-auth-models

> **Phase 1** : Authentification, Utilisateurs & RBAC  
> **Agent destinataire** : `@sentinel-data`  
> **Branche Git suggérée** : `feat/data-auth-models`

---

## Objectif

Définir les modèles de données SQLAlchemy 2.0 pour l'identité et le contrôle d'accès (`users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `sessions`) en conformité stricte avec `docs/data-model.md`, générer la migration Alembic asynchrone associée et fournir le seed des 4 rôles et permissions de référence définis dans `docs/rbac-matrix.md`.

---

## Dépendances

- Scaffold initial `apps/api/` opérationnel (Alembic configuré avec PostgreSQL 16 et moteur asynchrone).

---

## Contexte à lire

1. [`AGENTS.md`](file:///home/manassecodev/dev/Sentinel/AGENTS.md) — § 4.1 (Interdictions sur le modèle de données) et § 8.2 (Base de données).
2. [`docs/data-model.md`](file:///home/manassecodev/dev/Sentinel/docs/data-model.md) — Section 1 (*Identité & accès* : `users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `sessions`).
3. [`docs/rbac-matrix.md`](file:///home/manassecodev/dev/Sentinel/docs/rbac-matrix.md) — Définition des 4 rôles (`admin`, `operator`, `analyst`, `viewer`), 15 ressources et actions pour le seed.

---

## Arborescence exacte à produire

```text
apps/api/
├── app/
│   ├── models/
│   │   ├── __init__.py                # Export de tous les modèles pour autogenerate
│   │   ├── user.py                    # Modèle User (table `users`)
│   │   ├── role.py                    # Modèles Role, Permission, RolePermission, UserRole
│   │   └── session.py                 # Modèle Session (table `sessions`)
│   └── core/
│       └── seeds.py                   # Script/fonction idempotente pour insérer rôles & permissions
└── alembic/
    └── versions/
        └── <timestamp>_auth_and_rbac_tables.py  # Migration initiale Alembic
```

---

## Contraintes strictes

1. **Conformité absolue du schéma** :
   - Clé primaire `id` : UUID v7 (ou UUID standard compatible avec la convention Sentinel).
   - Horodatages `created_at` et `updated_at` en `timestamptz` (UTC).
   - `users.email` en type `citext` (insensible à la casse) avec contrainte `UNIQUE`.
   - `users.password_hash` en type `text` (conçu pour stocker le hash argon2id).
   - `sessions.ip` en type `inet`.
   - `sessions.refresh_token_hash` en type `text`.
   - `sessions.revoked_at` et `sessions.expires_at` en `timestamptz`.
2. **Conventions SQLAlchemy 2.0** :
   - Utilisation exclusive de `Mapped[...]` et `mapped_column(...)`.
   - Héritage de `Base` (`app.models.base.Base`).
   - Déclaration explicite des relations (`relationship`, `back_populates` ou `lazy="selectin"` selon besoin).
3. **Alembic** :
   - Migration réversible obligatoire (`upgrade()` et `downgrade()`).
   - Extensions PostgreSQL activées dans la migration si non présentes (`CREATE EXTENSION IF NOT EXISTS citext;`).
4. **Idempotence du Seed** :
   - Le seed des rôles (`admin`, `operator`, `analyst`, `viewer`) et des permissions déduites de la matrice doit être ré-exécutable sans erreur (clause `ON CONFLICT DO NOTHING`).

---

## Critères de succès

- [ ] `uv run alembic revision --autogenerate -m "create auth and rbac tables"` produit la migration conforme.
- [ ] `uv run alembic upgrade head` s'exécute sans erreur sur PostgreSQL 16 (port 5433).
- [ ] `uv run alembic downgrade -1` puis `uv run alembic upgrade head` valide la réversibilité stricte.
- [ ] L'exécution du seed initialise les 4 rôles et leurs associations de permissions selon `docs/rbac-matrix.md`.
- [ ] `uv run ruff check .` et `uv run mypy app` passent sans erreur.

---

## Interdictions

- ❌ Ne jamais créer de table non documentée dans `docs/data-model.md` (interdit de créer `user_site_access` en V1).
- ❌ Ne jamais ajouter, renommer ou supprimer une colonne.
- ❌ Ne pas coder de logique applicative HTTP ou de route FastAPI.
- ❌ Ne pas toucher aux fichiers sacrés (`docs/*`, `AGENTS.md`, etc.).

---

## En cas de blocage

Si une incohérence de type apparaît entre PostgreSQL (`citext`, `inet`) et SQLAlchemy 2.0 / Alembic :
1. Consulter les types de dialecte PostgreSQL de SQLAlchemy (`sqlalchemy.dialects.postgresql.CITEXT`, `INET`, `UUID`).
2. S'arrêter et signaler à l'humain si un ajustement d'extension est requis.

---

## Livrable attendu

1. Modèles SQLAlchemy déclarés dans `apps/api/app/models/`.
2. Fichier de migration dans `apps/api/alembic/versions/`.
3. Script de seed dans `apps/api/app/core/seeds.py`.
4. Rapport d'exécution attestant du succès d'`alembic upgrade head`.

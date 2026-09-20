# Sentinel — Matrice RBAC

> Version 1.0 — Phase 0
> Source de vérité pour le contrôle d'accès côté serveur.

## Ressources

`user` · `role` · `site` · `zone` · `device` · `sensor` · `event` ·
`rule` · `alert` · `notification` · `analysis` · `report` · `ai` ·
`audit` · `setting`

## Actions

`read` · `create` · `update` · `delete` · `archive` · `execute` ·
`acknowledge` · `assign` · `export` · `manage`

---

## Rôles

| code | label | description |
|---|---|---|
| `admin` | Administrateur | Configuration globale, utilisateurs, règles, paramètres, audit |
| `operator` | Opérateur | Supervision quotidienne, dashboard, événements, alertes, acquittement |
| `analyst` | Analyste | Historique, analytics, rapports, exports |
| `viewer` | Lecteur | Consultation en lecture seule des vues autorisées |

---

## Matrice

| Ressource | Admin | Opérateur | Analyste | Lecteur |
|---|---|---|---|---|
| user | manage | — | — | — |
| role | manage | — | — | — |
| site | manage | read | read | read |
| zone | manage | read, update(status) | read | read |
| device | manage | read | read | read |
| sensor | manage | read | read | read |
| event | read, export | read | read, export | read |
| rule | manage | read | read | — |
| alert | manage | read, acknowledge, assign, update, export | read, export | read |
| notification | manage | read | read | — |
| analysis | manage | read | read, create, execute, export | — |
| report | manage | read, create, export | read, create, export | — |
| ai | manage | execute | execute | — |
| audit | read | — | read | — |
| setting | manage | — | — | — |

---

## Portée

- **V1** : permissions globales — un opérateur voit tous les sites.
- **V1.1** : table `user_site_access` activée. La portée devient : globale
  OU restreinte à une liste de sites par utilisateur.
- **Implémentation** : décorateur FastAPI `@requires("alert:acknowledge")`
  + dépendance `get_current_user` qui charge les permissions effectives.

---

## Règles transverses

1. Toute route `/api/v1/*` est protégée, sauf :
   - `POST /auth/login`
   - `POST /auth/refresh`
   - `GET /health`
2. Le RBAC est vérifié **côté serveur uniquement**. Le front masque l'UI,
   mais ne décide jamais.
3. Toute action sensible (`manage`, `delete`, `acknowledge`) génère une
   entrée dans `audit_logs`.
4. Le rôle `admin` bypasse les vérifications mais reste audité.
5. Un utilisateur sans rôle actif est refusé (401).
6. Un utilisateur authentifié sans permission sur la ressource est refusé (403).

---

## Codes de permission

Format : `{resource}:{action}`

Exemples :
- `site:read`, `site:manage`
- `alert:acknowledge`, `alert:assign`
- `rule:manage`
- `ai:execute`
- `audit:read`

La liste complète est générée à partir de la matrice ci-dessus.
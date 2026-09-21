# Agents Antigravity — Sentinel

## Les 9 agents

| # | Agent | Modèle | Rôle |
|---|---|---|---|
| 1 | sentinel-architect | pro | Rédige les briefs d exécution |
| 2 | sentinel-backend | pro | Écrit le code FastAPI |
| 3 | sentinel-frontend | pro | Écrit le code Next.js |
| 4 | sentinel-data | pro | Modèles SQLAlchemy + migrations Alembic |
| 5 | sentinel-security | pro | Auth, RBAC, sessions, sécurité |
| 6 | sentinel-tests | flash | Tests pytest + frontend |
| 7 | sentinel-ai | pro | Orchestration IA + outils autorisés |
| 8 | sentinel-docs | flash | Documentation technique |
| 9 | sentinel-reviewer | pro | Revue de code, conformité, sécurité |

## Flux de travail

1. sentinel-architect produit docs/briefs/NN-<slug>.md
2. sentinel-data crée modèles + migrations si requis
3. sentinel-security auth / RBAC si requis
4. sentinel-backend implémente routes + services
5. sentinel-frontend écrans + composants
6. sentinel-ai outils IA si requis
7. sentinel-tests tests backend + frontend
8. sentinel-reviewer relit, rapporte, approuve ou bloque
9. Humain commit et tâche suivante

## Règles communes

- Lire AGENTS.md avant toute action.
- Ne jamais modifier les fichiers sacrés.
- S arrêter et signaler un blocage plutôt qu inventer.
- Jamais de commande git sauf sentinel-reviewer en lecture seule.
- Aucun secret dans le code.

## Utilisation dans Antigravity

@sentinel-architect Découpe la Phase 1 en briefs.
@sentinel-backend Exécute le brief : docs/briefs/01-api-scaffold.md
@sentinel-frontend Exécute le brief : docs/briefs/10-web-dashboard.md
@sentinel-tests Écris les tests pour l endpoint /api/v1/health
@sentinel-reviewer Relis le diff de la branche feat/api-scaffold

## Maquettes

Produites plus tard via Google Stitch, MCP connecté à Antigravity.
sentinel-frontend se conforme aux maquettes Stitch quand elles existent.

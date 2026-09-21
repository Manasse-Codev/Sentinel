# Notes de test — Sentinel

> Référence pratique pour les développeurs et les agents.
> Contient uniquement des informations opérationnelles vérifiées.

## 1. Emails de test valides

Le projet utilise `email-validator` en mode strict via Pydantic.
Certains TLD réservés sont refusés.

**Valides :**
- `admin@example.com`
- `user@example.com`
- `<anything>@example.com`

**Refusés par la validation :**
- `@sentinel.local` — `.local` est réservé mDNS (RFC 6762)
- `@sentinel.test` — `.test` refusé par email-validator
- `@anything.invalid` — refusé
- `@anything.localhost` — refusé

**Règle :** pour tout test manuel ou automatisé, utiliser `@example.com`.

## 2. Ports locaux

| Service | Port hôte | Port conteneur |
|---|---|---|
| PostgreSQL | 5433 | 5432 |
| Redis | 6381 | 6379 |
| API (uvicorn) | 8000 | — |

Ces ports sont dédiés à Sentinel et évitent les conflits avec les autres projets de la machine.

## 3. Commandes utiles

Toutes les commandes backend se lancent depuis `apps/api/`.

### Lancer le serveur

```bash
uv run uvicorn app.main:app --port 8000
```

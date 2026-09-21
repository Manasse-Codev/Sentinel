# Brief — 04-rbac-dependency

> **Phase 1** : Authentification, Utilisateurs & RBAC  
> **Agent destinataire** : `@sentinel-security`  
> **Branche Git suggérée** : `feat/rbac-dependency`

---

## Objectif

Construire le système de contrôle d'accès basé sur les rôles (RBAC) côté serveur pour FastAPI : dépendance `get_current_user` extrayant et validant le token JWT, chargement des rôles et des permissions effectives, et fonction/dépendance `@requires("<resource>:<action>")` appliquant strictement la matrice de droits définie dans `docs/rbac-matrix.md`.

---

## Dépendances

- `docs/briefs/01-data-auth-models.md` (modèles `Role`, `Permission`, `UserRole`, `RolePermission`).
- `docs/briefs/02-security-core.md` (décodage et validation JWT).
- `docs/briefs/03-auth-endpoints.md` (cycle d'authentification utilisateur).

---

## Contexte à lire

1. [`AGENTS.md`](file:///home/manassecodev/dev/Sentinel/AGENTS.md) — § 4.2 (RBAC obligatoire), § 8.1 (FastAPI deps), § 8.6 (Sécurité).
2. [`docs/rbac-matrix.md`](file:///home/manassecodev/dev/Sentinel/docs/rbac-matrix.md) — Source unique de vérité : 4 rôles (`admin`, `operator`, `analyst`, `viewer`), 15 ressources, 10 actions, règles transverses.

---

## Arborescence exacte à produire

```text
apps/api/
├── app/
│   ├── core/
│   │   ├── deps.py                    # Dépendance get_current_user, get_current_active_user
│   │   └── rbac.py                    # Dépendance requires(permission_code) / PermissionChecker
│   └── schemas/
│       └── rbac.py                    # Schéma UserContext avec rôles et ensemble de permissions
```

---

## Contraintes strictes

1. **Vérification côté serveur uniquement** :
   - Le RBAC s'applique au niveau des routes FastAPI via injection de dépendance (`Depends(requires("resource:action"))`).
2. **Résolution des droits** :
   - `get_current_user` valide le token Bearer, extrait l'utilisateur, vérifie `is_active == True` et que le compte n'est pas verrouillé (`locked_until IS NULL` ou expiré).
   - Chargement optimisé des rôles et permissions associés (éviter le problème N+1 via jointure appropriée).
3. **Règles transverses de la matrice** :
   - Règle 4 : Le rôle `admin` bypasse les vérifications de permissions spécifiques (accès automatique accordé à toute ressource), mais l'utilisateur reste identifié pour l'audit.
   - Règle 5 : Un utilisateur sans rôle actif est immédiatement rejeté avec code `401 Unauthorized`.
   - Règle 6 : Un utilisateur authentifié qui ne possède pas la permission requise (`resource:action` ou `resource:manage`) est rejeté avec code `403 Forbidden` (`"Permissions insuffisantes"`).
4. **Format des codes de permission** :
   - Format standard : `{resource}:{action}` (ex: `user:manage`, `site:read`, `alert:acknowledge`).
   - La permission `{resource}:manage` octroie implicitement toutes les actions sur cette ressource.

---

## Critères de succès

- [ ] Un token invalide ou absent sur une route protégée renvoie `401 Unauthorized`.
- [ ] Un utilisateur doté du rôle `viewer` accédant à une route protégée par `requires("user:manage")` reçoit `403 Forbidden`.
- [ ] Un utilisateur doté du rôle `admin` accédant à une route protégée par n'importe quelle permission est autorisé.
- [ ] Un utilisateur ayant la permission explicite passe la barrière sans latence excessive.
- [ ] `uv run ruff check .` et `uv run mypy app` passent à 100%.

---

## Interdictions

- ❌ Interdiction de désactiver le RBAC pour des tests locaux ou en dev.
- ❌ Interdiction de faire reposer la moindre décision d'autorisation sur le frontend.
- ❌ Pas d'injection SQL dans le chargement des permissions.

---

## En cas de blocage

Si la syntaxe de permission composée prête à confusion :
- Se référer exclusivement à `docs/rbac-matrix.md` (section *Codes de permission*).

---

## Livrable attendu

1. Dépendances d'authentification dans `apps/api/app/core/deps.py`.
2. Moteur de vérification de permissions dans `apps/api/app/core/rbac.py`.
3. Modèles de contexte utilisateur dans `apps/api/app/schemas/rbac.py`.

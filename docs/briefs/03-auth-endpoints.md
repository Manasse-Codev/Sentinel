# Brief — 03-auth-endpoints

> **Phase 1** : Authentification, Utilisateurs & RBAC  
> **Agent destinataire** : `@sentinel-backend`  
> **Branche Git suggérée** : `feat/auth-endpoints`

---

## Objectif

Implémenter l'ensemble des endpoints d'authentification sous le préfixe `/api/v1/auth` (`login`, `refresh`, `logout`, `me`) selon les règles strictes de séparation en couches de Sentinel (route → service → repository), avec validation Pydantic en entrée et en sortie.

---

## Dépendances

- `docs/briefs/01-data-auth-models.md` (modèles `User`, `Session`, `Role`).
- `docs/briefs/02-security-core.md` (hachage argon2id, utilitaires JWT et gestion du lockout).

---

## Contexte à lire

1. [`AGENTS.md`](file:///home/manassecodev/dev/Sentinel/AGENTS.md) — § 4.2 (API & RBAC), § 5.3 (Nommage), § 5.4 (Structure d'un module backend), § 8.1 (FastAPI).
2. [`docs/data-model.md`](file:///home/manassecodev/dev/Sentinel/docs/data-model.md) — Attributs des tables `users` et `sessions`.
3. [`docs/rbac-matrix.md`](file:///home/manassecodev/dev/Sentinel/docs/rbac-matrix.md) — § Règles transverses (routes publiques `/auth/login`, `/auth/refresh`).

---

## Arborescence exacte à produire

```text
apps/api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py                # Endpoints FastAPI /login, /refresh, /logout, /me
│   │       └── router.py              # Inclusion du routeur auth sous /auth
│   ├── schemas/
│   │   ├── auth.py                    # Schémas LoginRequest, TokenResponse, RefreshRequest
│   │   └── user.py                    # Schémas UserResponse, UserProfileResponse
│   ├── services/
│   │   └── auth_service.py            # Logique métier d'authentification et session
│   └── repositories/
│       ├── user_repository.py         # Requêtes SQLAlchemy pour User
│       └── session_repository.py      # Requêtes SQLAlchemy pour Session
```

---

## Contraintes strictes

1. **Routes & Méthodes HTTP** :
   - `POST /api/v1/auth/login` : Public. Reçoit email + mot de passe, vérifie le statut du compte (actif, non verrouillé), valide le mot de passe, met à jour `last_login_at` et réinitialise `failed_login_count`, crée une entrée `sessions` et retourne `access_token` + `refresh_token` + `user`.
   - `POST /api/v1/auth/refresh` : Public. Reçoit le refresh token, vérifie sa validité et que la session n'est ni expirée ni révoquée (`revoked_at IS NULL`), émet un nouvel `access_token`.
   - `POST /api/v1/auth/logout` : Protégé. Invalide la session courante en fixant `revoked_at = now()`.
   - `GET /api/v1/auth/me` : Protégé. Renvoie le profil complet de l'utilisateur connecté avec la liste de ses rôles et permissions.
2. **Séparation stricte des couches (§ 5.4)** :
   - La route ne manipule aucun SQL ni de session DB directe : elle appelle `auth_service`.
   - Le service orchestre la validation métier, le lockout, le hachage et appelle les repositories.
   - Les repositories encapsulent les requêtes SQLAlchemy asynchrones.
3. **Gestion des erreurs explicite** :
   - Mauvais identifiants : `401 Unauthorized` avec message générique `"Identifiants invalides"`.
   - Compte verrouillé : `423 Locked` ou `401` avec détail sur l'expiration du verrou.
   - Compte inactif : `403 Forbidden` (`"Compte désactivé"`).
   - Refresh token invalide ou révoqué : `401 Unauthorized`.
4. **Validation Pydantic** :
   - Validation stricte en entrée (`LoginRequest` avec email valide et mot de passe non vide).
   - Schéma de sortie systématique (`response_model=...`).

---

## Critères de succès

- [ ] L'appel `POST /api/v1/auth/login` avec identifiants corrects renvoie 200, les tokens et les données utilisateur.
- [ ] L'appel `POST /api/v1/auth/login` avec mauvais mot de passe incrémente `failed_login_count` et renvoie 401.
- [ ] 5 échecs consécutifs verrouillent le compte (`locked_until` renseigné) et bloquent les tentatives suivantes.
- [ ] `POST /api/v1/auth/refresh` prolonge la session valide avec un nouvel access token.
- [ ] `POST /api/v1/auth/logout` révoque la session en DB.
- [ ] `uv run ruff check .` et `uv run mypy app` passent à 100%.

---

## Interdictions

- ❌ Interdiction absolue d'exécuter des requêtes SQL brutes non paramétrées ou directement dans les routes.
- ❌ Interdiction de renvoyer le `password_hash` dans un quelconque schéma Pydantic de sortie.
- ❌ Pas de contournement de la vérification de compte actif.
- ❌ Pas de commande `print()` (utiliser `structlog`).

---

## En cas de blocage

Si l'extraction de l'IP du client ou du User-Agent pose question dans FastAPI :
- Utiliser `request.client.host` et `request.headers.get("user-agent")`.

---

## Livrable attendu

1. Routes auth dans `apps/api/app/api/v1/auth.py`.
2. Service métier dans `apps/api/app/services/auth_service.py`.
3. Repositories dans `apps/api/app/repositories/`.
4. Schémas Pydantic dans `apps/api/app/schemas/auth.py` et `user.py`.

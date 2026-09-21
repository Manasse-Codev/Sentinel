# Brief — 02-security-core

> **Phase 1** : Authentification, Utilisateurs & RBAC  
> **Agent destinataire** : `@sentinel-security`  
> **Branche Git suggérée** : `feat/security-core`

---

## Objectif

Mettre en place la couche cryptographique et de sécurité centrale de Sentinel : hachage de mot de passe avec **argon2id**, génération et validation des tokens JWT (Access Token court) et tokens opaques sécurisés (Refresh Token haché en base), et gestion des règles de verrouillage de compte (lockout après échecs répétés).

---

## Dépendances

- `docs/briefs/01-data-auth-models.md` complété (tables `users` et `sessions` existantes).

---

## Contexte à lire

1. [`AGENTS.md`](file:///home/manassecodev/dev/Sentinel/AGENTS.md) — § 4.3 (Sécurité) et § 8.6 (Hachage argon2id, tokens courts, sessions).
2. [`docs/data-model.md`](file:///home/manassecodev/dev/Sentinel/docs/data-model.md) — Colonnes `users.password_hash`, `users.failed_login_count`, `users.locked_until`, `sessions.refresh_token_hash`.
3. [`.env.example`](file:///home/manassecodev/dev/Sentinel/.env.example) — Variables `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`.

---

## Arborescence exacte à produire

```text
apps/api/
├── app/
│   ├── core/
│   │   └── security.py                # Fonctions argon2id (hash, verify) et JWT (create, decode)
│   ├── schemas/
│   │   └── token.py                   # Schémas Pydantic Token, TokenPayload, RefreshTokenRequest
│   └── services/
│       └── security_service.py        # Logique de lockout (calcul failed_login_count, locked_until)
```

---

## Contraintes strictes

1. **Hachage obligatoire avec argon2id** :
   - Utiliser `pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")` ou `argon2-cffi`.
   - Tout mot de passe brut en transit ne doit jamais persister ni être loggué.
2. **Gestion des Tokens JWT** :
   - Payload de l'Access Token : `sub` (ID utilisateur string), `email`, `exp`, `iat`, `type="access"`.
   - Signature via `settings.JWT_SECRET` et algorithme `settings.JWT_ALGORITHM` (HS256).
   - Durée de vie stricte = `settings.ACCESS_TOKEN_EXPIRE_MINUTES` (15 min par défaut).
3. **Refresh Tokens** :
   - Génération d'une chaîne aléatoire cryptographiquement sûre (ex: `secrets.token_urlsafe(64)`).
   - Le refresh token n'est JAMAIS stocké en clair en DB : stockage de son empreinte SHA-256 ou hash dans `sessions.refresh_token_hash`.
4. **Verrouillage de compte (Anti-Bruteforce)** :
   - Paramétrer un seuil maximal d'échecs consécutifs (5 tentatives).
   - Au-delà du seuil, définir `locked_until = now() + timedelta(minutes=15)`.
   - Réinitialisation de `failed_login_count = 0` lors d'une authentification réussie.

---

## Critères de succès

- [ ] `verify_password("correct", get_password_hash("correct"))` renvoie `True`.
- [ ] `verify_password("wrong", get_password_hash("correct"))` renvoie `False`.
- [ ] La génération d'un token JWT respecte l'expiration définie et son décodage vérifie la signature.
- [ ] Un token expiré ou altéré lève une exception sécurisée spécifique.
- [ ] La fonction d'évaluation de lockout bloque les tentatives lorsque `locked_until` est dans le futur.
- [ ] `uv run ruff check .` et `uv run mypy app` passent à 100%.

---

## Interdictions

- ❌ Interdiction d'utiliser bcrypt, PBKDF2 ou SHA pour les mots de passe utilisateurs (argon2id exigé).
- ❌ Aucun secret ou token imprimé ou loggué (`print()` banni, pas de token dans `structlog`).
- ❌ Ne pas créer les routes HTTP dans ce brief (délégué à `sentinel-backend`).
- ❌ Ne pas désactiver de validation ou de vérification d'expiration.

---

## En cas de blocage

Si la bibliothèque de hachage requiert une dépendance binaire ou système :
- Vérifier la présence de `argon2-cffi` et `pyjwt` dans `pyproject.toml`. Les ajouter via `uv add argon2-cffi pyjwt` si nécessaire.

---

## Livrable attendu

1. Fonctions de hachage et de signature JWT dans `apps/api/app/core/security.py`.
2. Schémas de tokens Pydantic dans `apps/api/app/schemas/token.py`.
3. Logique de protection bruteforce dans `apps/api/app/services/security_service.py`.

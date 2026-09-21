# Brief — 05-tests-auth-rbac

> **Phase 1** : Authentification, Utilisateurs & RBAC  
> **Agent destinataire** : `@sentinel-tests`  
> **Branche Git suggérée** : `test/auth-rbac`

---

## Objectif

Concevoir et exécuter une suite complète de tests automatisés (unitaires et d'intégration via `pytest-asyncio` et `httpx`) validant le cycle de vie de l'authentification (login, lockout, refresh, logout, me) et la conformité stricte de la matrice RBAC (codes HTTP 200, 401, 403 pour les 4 rôles Sentinel).

---

## Dépendances

- `docs/briefs/01-data-auth-models.md`
- `docs/briefs/02-security-core.md`
- `docs/briefs/03-auth-endpoints.md`
- `docs/briefs/04-rbac-dependency.md`

---

## Contexte à lire

1. [`AGENTS.md`](file:///home/manassecodev/dev/Sentinel/AGENTS.md) — § 7 (Definition of Done) et § 8.1 (Tests FastAPI).
2. [`docs/rbac-matrix.md`](file:///home/manassecodev/dev/Sentinel/docs/rbac-matrix.md) — Tableau de la matrice des 4 rôles et règles transverses 1 à 6.
3. [`docs/data-model.md`](file:///home/manassecodev/dev/Sentinel/docs/data-model.md) — Schéma des tables d'identité.

---

## Arborescence exacte à produire

```text
apps/api/tests/
├── conftest.py                        # Fixtures pytest (client httpx, session DB de test, helpers)
├── factories.py                       # Helpers de création d'utilisateurs avec rôles (admin, operator, etc.)
├── api/
│   └── test_auth.py                   # Tests d'intégration des endpoints /api/v1/auth/*
└── core/
    ├── test_security.py               # Tests unitaires argon2id, création et validation JWT
    └── test_rbac.py                   # Tests de la dépendance RBAC et matrice des permissions
```

---

## Contraintes strictes

1. **Isolation des tests** :
   - Chaque test doit s'exécuter dans une transaction propre ou avec nettoyage des données de test afin d'éviter tout effet de bord.
2. **Couverture obligatoire des cas limites** :
   - Login : succès, mauvais mot de passe, email inexistant, compte inactif.
   - Bruteforce : 5 tentatives échouées consécutives entraînent un verrouillage temporaire (tentative 6 rejetée).
   - Refresh token : succès, token révoqué, token altéré/expiré.
   - Logout : révocation effective vérifiée en tentant un nouveau refresh.
3. **Validation rigoureuse de la Matrice RBAC** :
   - Tester explicitement les 4 rôles (`admin`, `operator`, `analyst`, `viewer`).
   - Tester qu'un `admin` passe sur n'importe quelle ressource protégée.
   - Tester qu'un `viewer` voulant accéder à une ressource protégée (ex: `user:manage`) reçoit un code HTTP `403`.
   - Tester qu'un utilisateur sans rôle associé reçoit un code HTTP `401`.
   - Tester qu'une requête sans token d'autorisation sur route protégée reçoit un code HTTP `401`.
4. **Zéro régression** :
   - Le test existant [`tests/test_health.py`](file:///home/manassecodev/dev/Sentinel/apps/api/tests/test_health.py) doit continuer à passer sans altération.

---

## Critères de succès

- [ ] `uv run pytest` exécute l'ensemble des tests avec **100% de succès**.
- [ ] Tous les codes HTTP attendus (`200`, `401`, `403`, `422`) sont vérifiés avec assertions sur les payloads de sortie.
- [ ] Aucun warning bloquant ni fuite de session de test.
- [ ] `uv run ruff check .` et `uv run mypy app` passent à 100%.

---

## Interdictions

- ❌ Interdiction de supprimer, masquer ou affaiblir un test qui échoue.
- ❌ Interdiction de modifier le code de production dans ce brief sans justification documentée.
- ❌ Pas de dépendance vers des mocks non justifiés pour la base de données PostgreSQL de test (utiliser les conteneurs existants ou base isolée).

---

## En cas de blocage

Si une collision de données se produit entre tests :
- Utiliser des adresses emails générées aléatoirement (`f"user_{uuid4()}@sentinel.local"`) dans les factories.

---

## Livrable attendu

1. Fixtures et factories enrichies dans `apps/api/tests/conftest.py` et `factories.py`.
2. Fichiers de tests dans `apps/api/tests/api/` et `apps/api/tests/core/`.
3. Rapport d'exécution `pytest` complet détaillant le nombre de tests passés.

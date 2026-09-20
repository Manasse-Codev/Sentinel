# AGENTS.md

> Règles de travail pour les agents IA intervenant sur le projet Sentinel.
> Ce fichier est **normatif**. Il prime sur toute intuition ou convention par défaut.
> Dernière mise à jour : Phase 0.

---

## 1. Contexte du projet

**Sentinel** est une plateforme web modulaire de supervision temps réel.
Elle centralise des capteurs et des événements, applique des règles de
détection déterministes, gère des alertes, produit des analyses et
fournit un assistant IA isolé.

**Stack imposée** — ne pas en changer sans validation humaine :

| Couche | Technologie |
|---|---|
| Frontend | Next.js + TypeScript + Tailwind CSS |
| Backend | Python + FastAPI + Pydantic |
| ORM | SQLAlchemy 2.0 + Alembic |
| Base de données | PostgreSQL 16 |
| Cache / temps réel | Redis 7 + WebSocket |
| Data | Pandas, NumPy, scikit-learn |
| IA | LLM via couche d'orchestration dédiée |
| Tests | Pytest, tests API, E2E |
| Infra | Docker / Docker Compose |
| CI/CD | GitHub Actions |

---

## 2. Ordre de lecture obligatoire

Avant **toute** action sur le code, lire dans cet ordre :

1. `README.md` — vision, stack, principes
2. `AGENTS.md` — ce fichier
3. `docs/README.md` — index de la documentation
4. `docs/data-model.md` — schéma PostgreSQL (source de vérité)
5. `docs/rbac-matrix.md` — contrôle d'accès
6. `docs/rule-engine-spec.md` — moteur de règles
7. `docs/ai-tools-spec.md` — isolation IA
8. `docs/anomaly-detection-spec.md` — détection d'anomalies

**Ne jamais coder une entité, un endpoint ou une règle qui n'est pas dans ces documents.**

---

## 3. Fichiers sacrés (ne pas modifier sans validation humaine)

Ces fichiers sont la **source de vérité**. Un agent ne peut pas les modifier
de sa propre initiative :

- `README.md`
- `AGENTS.md`
- `docs/data-model.md`
- `docs/rbac-matrix.md`
- `docs/rule-engine-spec.md`
- `docs/ai-tools-spec.md`
- `docs/anomaly-detection-spec.md`
- `docker-compose.yml`
- `pnpm-workspace.yaml`
- `turbo.json`

Si un agent estime qu'un de ces fichiers doit changer, il **s'arrête** et
signale le besoin à l'humain. Il ne modifie pas.

---

## 4. Interdictions explicites

### 4.1 Sur le modèle de données

- ❌ Créer une table qui n'est pas dans `docs/data-model.md`
- ❌ Ajouter une colonne sans mise à jour du schéma documenté
- ❌ Renommer une colonne existante
- ❌ Supprimer une table ou une colonne
- ❌ Utiliser un type PostgreSQL différent de celui documenté

### 4.2 Sur l'API

- ❌ Créer un endpoint hors du préfixe `/api/v1/`
- ❌ Créer un endpoint non listé dans les specs
- ❌ Exposer un endpoint sans vérification RBAC (sauf `/health`, `/auth/login`, `/auth/refresh`)
- ❌ Renvoyer un objet sans schéma Pydantic de sortie
- ❌ Accepter un payload sans validation Pydantic en entrée

### 4.3 Sur la sécurité

- ❌ Commiter un secret, token, mot de passe, clé API
- ❌ Désactiver une vérification RBAC « pour tester »
- ❌ Logger un mot de passe, un token ou une donnée personnelle
- ❌ Donner à l'IA un accès direct à la base de données
- ❌ Exécuter une action physique critique depuis une sortie LLM

### 4.4 Sur l'IA

- ❌ Ajouter un outil IA non listé dans `docs/ai-tools-spec.md`
- ❌ Laisser l'IA écrire en base
- ❌ Laisser l'IA contourner le RBAC
- ❌ Appeler un outil IA sans journaliser dans `ai_tool_calls`

### 4.5 Sur le code

- ❌ Mettre de la logique métier critique dans le frontend
- ❌ Utiliser `any` en TypeScript sans justification en commentaire
- ❌ Écrire une requête SQL brute sans paramétrage
- ❌ Utiliser `print()` en Python (utiliser `logging`)
- ❌ Laisser du code mort, du TODO sans issue associée, du debug

---

## 5. Conventions obligatoires

### 5.1 Branches

```
feat/<scope>          nouvelle fonctionnalité
fix/<scope>           correction
refactor/<scope>      refactorisation
docs/<scope>          documentation
test/<scope>          tests
chore/<scope>         maintenance
security/<scope>      sécurité
```

Exemples :
- `feat/auth-rbac`
- `feat/sensor-simulator`
- `fix/duplicate-events`
- `security/restrict-rule-management`

### 5.2 Commits — Conventional Commits

```
<type>: <description courte à l'impératif>
```

Types autorisés : `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `security`.

Exemples :
- `feat: add sensor simulator`
- `fix: prevent duplicate events`
- `security: restrict rule management`
- `test: add alert engine tests`

**Un commit = une intention.** Pas de `wip`, pas de `fix stuff`, pas de
commit fourre-tout.

### 5.3 Nommage

| Élément | Convention | Exemple |
|---|---|---|
| Tables SQL | snake_case pluriel | `sensor_readings` |
| Colonnes SQL | snake_case | `occurred_at` |
| Modèles Python | PascalCase | `SensorReading` |
| Fonctions Python | snake_case | `get_zone_status` |
| Fichiers Python | snake_case | `zone_service.py` |
| Composants React | PascalCase | `ZoneCard.tsx` |
| Hooks React | camelCase préfixé `use` | `useZoneStatus.ts` |
| Routes API | kebab-case pluriel | `/api/v1/sensor-readings` |
| Variables d'env | SCREAMING_SNAKE | `DATABASE_URL` |

### 5.4 Structure d'un module backend

```
app/
├── api/v1/<resource>.py       # routes, validation, RBAC
├── services/<resource>.py     # logique métier
├── repositories/<resource>.py # accès DB
├── models/<resource>.py       # SQLAlchemy
└── schemas/<resource>.py      # Pydantic
```

**Séparation stricte** : la route ne fait pas de SQL, le repository ne fait
pas de RBAC, le service ne connaît pas HTTP.

---

## 6. Workflow d'une feature

Pour **chaque** fonctionnalité (F01 → F16 du cahier des charges) :

1. **Lire la spec** correspondante dans `docs/`
2. **Créer une branche** : `feat/<scope>`
3. **Écrire les tests d'abord** quand c'est pertinent
4. **Implémenter** en respectant la structure § 5.4
5. **Vérifier** :
   - lint passe
   - tests passent
   - aucun secret commité
   - RBAC appliqué
   - validation Pydantic en entrée/sortie
   - erreurs gérées explicitement
   - logs utiles (sans données sensibles)
6. **Commit** avec un message Conventional Commits
7. **Push** et ouvrir une PR

**Interdit** : travailler sur deux features en parallèle dans la même branche.

---

## 7. Definition of Done

Une fonctionnalité n'est **terminée** que si elle possède :

- [ ] implémentation conforme à la spec
- [ ] validation backend (Pydantic)
- [ ] gestion des erreurs explicite
- [ ] tests pertinents (unitaires + intégration)
- [ ] logs utiles (sans secrets)
- [ ] contrôle d'accès RBAC
- [ ] documentation minimale (docstring ou doc)
- [ ] interface responsive (si UI)
- [ ] vérification manuelle effectuée
- [ ] aucun secret exposé

Si un seul point manque, la feature n'est **pas** terminée.

---

## 8. Règles spécifiques par domaine

### 8.1 Backend (FastAPI)

- Toute route est asynchrone (`async def`) sauf justification
- Toute route utilise une dépendance d'injection pour la session DB
- Toute route protégée utilise `Depends(get_current_user)` + `@requires("<perm>")`
- Aucun `try/except` silencieux — logguer et propager
- Les erreurs métier remontent en `HTTPException` avec un code clair

### 8.2 Base de données

- Migrations Alembic **uniquement**, jamais de DDL à la main
- Une migration = un changement logique
- Les migrations sont réversibles (`upgrade` + `downgrade`)
- Pas de modification d'une migration déjà mergée
- Les index sont créés dans la même migration que la table

### 8.3 Frontend (Next.js)

- App Router uniquement (pas de Pages Router)
- Server Components par défaut, Client Components seulement si nécessaire
- Pas d'appel direct à la DB depuis le frontend
- Les appels API passent par un client typé généré depuis OpenAPI (ou fetch typé manuel)
- Le front masque l'UI non autorisée, mais **ne décide jamais** des permissions

### 8.4 IA

- Chaque outil IA est une fonction décorée `@ai_tool`
- Chaque appel est journalisé dans `ai_tool_calls`
- Le LLM ne reçoit que les outils autorisés pour l'utilisateur courant
- Les sorties structurées passent par Pydantic
- Le provider LLM est abstrait derrière une interface `LLMProvider`

### 8.5 Temps réel

- WebSocket authentifié (token en query ou header)
- Redis Streams pour la persistance des messages diffusés
- Un événement diffusé = un événement persisté en DB (pas de divergence)

### 8.6 Sécurité

- Mots de passe hachés avec **argon2id**
- Tokens JWT courts (access) + refresh token en DB (révocable)
- Rate limiting sur les endpoints sensibles
- Taille maximale des payloads configurée
- Toute action sensible → `audit_logs`

---

## 9. Ce qu'un agent doit faire s'il est bloqué

Si une information manque, si une spec est ambiguë, si un choix n'est pas
tranché :

1. **Ne pas inventer**
2. **Ne pas coder à moitié**
3. **S'arrêter**
4. **Signaler** le blocage à l'humain avec :
   - ce qui était demandé
   - ce qui manque
   - les options possibles
   - une recommandation

Un agent qui invente est pire qu'un agent qui s'arrête.

---

## 10. Ce qu'un agent ne doit JAMAIS faire

- Modifier un fichier sacré sans validation
- Commiter un secret
- Désactiver une sécurité
- Inventer une table, un endpoint ou une règle
- Mélanger plusieurs features dans une branche
- Faire un `git push --force` sur `main`
- Faire un `git rebase` sur une branche partagée
- Supprimer un test qui échoue (le réparer ou signaler)
- Ignorer un warning de lint sans justification

---

## 11. Rappel des principes d'architecture

Extraits du README, **non négociables** :

1. Séparer présentation, métier et infrastructure.
2. Ne jamais mettre la logique métier critique uniquement dans le frontend.
3. Valider les données à l'entrée et à la sortie.
4. Versionner l'API.
5. Rendre les traitements longs asynchrones.
6. Rendre les événements idempotents lorsque nécessaire.
7. Tracer les opérations sensibles.
8. Isoler les capacités IA derrière des outils explicitement autorisés.
9. Ne jamais donner à l'IA un accès arbitraire au système.
10. Préparer l'application à fonctionner sans caméra réelle grâce au simulateur.

---

## 12. Phases du projet

| Phase | Contenu |
|---|---|
| 0 | Cadrage, architecture, design system, dépôt Git |
| 1 | Auth + utilisateurs + RBAC |
| 2 | Sites + zones + capteurs + simulateur + ingestion |
| 3 | Temps réel + dashboard + historique |
| 4 | Moteur de règles + alertes + notifications |
| 5 | Analytics + anomalies |
| 6 | Assistant IA + rapports |
| 7 | Sécurité + tests + CI/CD + déploiement |

**Un agent ne travaille que sur la phase en cours.** Pas d'anticipation.

---

## 13. Contact et escalade

Toute question, ambiguïté ou blocage doit être remonté à l'humain
responsable du projet. Les agents n'ont pas autorité pour trancher seuls
les décisions structurantes (schéma DB, RBAC, sécurité, IA).

---

**Sentinel — Observe. Understand. Respond.**
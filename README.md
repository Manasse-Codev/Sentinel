# SENTINEL

> Plateforme intelligente de supervision, détection d’événements et d’analyse.

Sentinel est une plateforme web modulaire destinée à centraliser des capteurs et des événements, superviser un environnement en temps réel, appliquer des règles de détection, gérer les alertes et produire des analyses. Une couche IA vient compléter le système pour l’explication, la synthèse et l’exploration des données.

## 1. Vision

```text
Capteurs / Simulateur / Sources externes
                |
                v
        Event Ingestion
                |
                v
        Event Processing
          /          \
         v            v
   Rule Engine     Analytics
         |            |
         v            v
      Alerts      Anomalies
          \          /
           \        /
            v      v
             Dashboard
                 |
                 v
             AI Assistant
```

## 2. Architecture

```text
sentinel/
├── apps/
│   ├── web/                    # Next.js / TypeScript
│   └── api/                    # FastAPI / Python
├── services/
│   ├── event-engine/           # normalisation et traitement
│   ├── rule-engine/            # règles et déclencheurs
│   ├── analytics/              # statistiques et anomalies
│   └── ai/                     # orchestration IA et outils autorisés
├── packages/
│   ├── ui/                     # composants partagés
│   ├── schemas/                # contrats et schémas
│   └── config/                 # configuration partagée
├── infra/
│   ├── docker/
│   ├── migrations/
│   └── monitoring/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
└── README.md
```

## 3. Stack

| Couche | Technologie |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| ORM | SQLAlchemy |
| Base de données | PostgreSQL |
| Cache / temps réel | Redis + WebSocket |
| Data | Pandas, NumPy, scikit-learn |
| IA | LLM via couche d’orchestration dédiée |
| Tests | Pytest, tests API, E2E |
| Infrastructure | Docker / Docker Compose |
| CI/CD | GitHub Actions ou équivalent |
| Déploiement | Frontend cloud + backend Python + PostgreSQL managé |

## 4. Modules fonctionnels

- Authentification et RBAC
- Sites et zones
- Capteurs et équipements
- Simulateur d’événements
- Ingestion et normalisation
- Temps réel
- Moteur de règles
- Alertes
- Notifications
- Historique
- Analytics
- Détection d’anomalies
- Assistant IA
- Rapports
- Audit
- Paramètres

## 5. Principes d’architecture

1. Séparer présentation, métier et infrastructure.
2. Ne jamais mettre la logique métier critique uniquement dans le frontend.
3. Valider les données à l’entrée et à la sortie.
4. Versionner l’API.
5. Rendre les traitements longs asynchrones.
6. Rendre les événements idempotents lorsque nécessaire.
7. Tracer les opérations sensibles.
8. Isoler les capacités IA derrière des outils explicitement autorisés.
9. Ne jamais donner à l’IA un accès arbitraire au système.
10. Préparer l’application à fonctionner sans caméra réelle grâce au simulateur.

## 6. Flux d’un événement

```text
Sensor
  |
  v
POST /api/v1/events
  |
  v
Validation
  |
  v
Normalisation
  |
  +------> PostgreSQL
  |
  +------> Redis / WebSocket
  |
  v
Rule Engine
  |
  +---- normal ----> history
  |
  +---- anomaly ----> alert
                         |
                         v
                    notification
```

## 7. IA

L’IA ne remplace pas le moteur de règles.

Le moteur de règles reste déterministe pour les conditions critiques.

L’IA intervient principalement pour :

- expliquer un événement ;
- résumer une période ;
- rechercher dans l’historique ;
- comparer des situations ;
- interpréter des indicateurs ;
- produire des rapports ;
- assister l’opérateur.

Chaque outil IA doit avoir :
- un nom ;
- un schéma d’entrée ;
- un schéma de sortie ;
- des permissions ;
- des limites ;
- une journalisation.

## 8. Sécurité

- RBAC côté serveur.
- Hashage sécurisé des mots de passe.
- Secrets hors du dépôt Git.
- Validation Pydantic.
- Rate limiting.
- Contrôle de taille des payloads et fichiers.
- Protection des endpoints sensibles.
- Audit logs.
- Sessions/token avec expiration et révocation.
- Isolation des traitements IA.
- Pas d’action physique critique basée uniquement sur une sortie LLM.

## 9. Identité visuelle

### Direction

Sentinel doit avoir une identité **premium, technologique, précise et éditoriale**.

L’inspiration recherchée est proche des studios digitaux haut de gamme : composition généreuse, typographie expressive, grands titres, rythme visuel, interactions sobres et portfolio-like presentation. Elle doit cependant être transposée vers un produit de supervision technique.

### Mots-clés

`Precision` · `Signal` · `Control` · `Intelligence` · `Clarity` · `Trust`

### Direction UI

- Dark-first.
- Grille éditoriale.
- Typographie sans-serif contemporaine.
- Grandes zones de respiration.
- Accent lumineux réservé aux signaux système.
- Animations courtes et fonctionnelles.
- États visuels extrêmement clairs.
- Pas d’effet “hacker” cliché.
- Pas de surcharge néon.
- Pas de dashboard générique rempli de cartes.

### Palette indicative

```text
Background      #080A0D
Surface         #101419
Border          #20262D
Text             #F3F5F7
Muted            #8B949E
Signal           #7CFFB2
Warning          #FFC857
Critical         #FF5C69
```

Cette palette est une base de direction et devra être validée pendant la phase de design.

## 10. Roadmap de développement

### Phase 0
Architecture + design system + repository.

### Phase 1
Auth + utilisateurs + RBAC.

### Phase 2
Sites + zones + capteurs.

### Phase 3
Simulateur + ingestion + PostgreSQL.

### Phase 4
WebSocket + dashboard temps réel.

### Phase 5
Rules Engine + alertes.

### Phase 6
Analytics + anomalies.

### Phase 7
Assistant IA + rapports.

### Phase 8
Sécurité + tests + CI/CD + déploiement.

## 11. Installation locale

Prérequis :

- Node.js
- Python
- Docker
- Docker Compose
- Git

Puis :

```bash
git clone <repository>
cd sentinel
docker compose up -d
```

Frontend :

```bash
cd apps/web
npm install
npm run dev
```

Backend :

```bash
cd apps/api
uv sync
uv run fastapi dev
```

> Les commandes exactes seront figées lorsque le monorepo sera initialisé.

## 12. Variables d’environnement

Exemple :

```env
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
AI_API_KEY=
APP_ENV=development
```

Les secrets réels ne doivent jamais être commités.

## 13. Convention de développement

```text
feat/
fix/
refactor/
docs/
test/
chore/
security/
```

Commits :

```text
feat: add sensor simulator
fix: prevent duplicate events
security: restrict rule management
test: add alert engine tests
```

## 14. Definition of Done

Une fonctionnalité est considérée terminée lorsqu’elle possède :

- implémentation ;
- validation backend ;
- gestion des erreurs ;
- tests pertinents ;
- logs utiles ;
- contrôle d’accès ;
- documentation minimale ;
- interface responsive ;
- vérification manuelle ;
- aucun secret exposé.

## 15. Évolution future

- Intégration ESP32/Raspberry Pi.
- Caméras et flux vidéo.
- Connecteurs MQTT.
- Connecteurs industriels.
- Multi-tenant.
- Application mobile.
- Géolocalisation des équipements.
- Moteur prédictif avancé.
- Centre de commandes.
- Marketplace de connecteurs.

---

**Sentinel — Observe. Understand. Respond.**

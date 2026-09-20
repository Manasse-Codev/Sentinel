# Sentinel — Modèle de données

> Version 1.0 — Phase 0
> Source de vérité pour le schéma PostgreSQL.

## Conventions

- Toutes les tables possèdent `id` (UUID v7), `created_at`, `updated_at` (timestamptz).
- Soft delete via `archived_at` (nullable) sur les entités métier.
- Pas de suppression physique sauf sur `audit_logs` (rétention).
- Nommage : `snake_case`, tables au pluriel.
- Index sur toutes les FK et colonnes de filtre fréquent.
- Partitionnement mensuel pour les tables à haute volumétrie.

---

## 1. Identité & accès

### `users`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| email | citext UNIQUE | |
| password_hash | text | argon2id |
| full_name | text | |
| is_active | bool | default true |
| last_login_at | timestamptz | |
| failed_login_count | int | default 0 |
| locked_until | timestamptz | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `roles`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| code | text UNIQUE | `admin`, `operator`, `analyst`, `viewer` |
| label | text | |
| description | text | |

### `permissions`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| code | text UNIQUE | ex: `site:read`, `rule:write` |
| resource | text | |
| action | text | |

### `role_permissions`

| colonne | type | notes |
|---|---|---|
| role_id | uuid FK roles | PK composite |
| permission_id | uuid FK permissions | PK composite |

### `user_roles`

| colonne | type | notes |
|---|---|---|
| user_id | uuid FK users | PK composite |
| role_id | uuid FK roles | PK composite |

### `user_site_access`

> Préparé pour V1.1 — vide en V1.

| colonne | type | notes |
|---|---|---|
| user_id | uuid FK users | PK composite |
| site_id | uuid FK sites | PK composite |
| role_id | uuid FK roles | |

### `sessions`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK users | |
| refresh_token_hash | text | |
| user_agent | text | |
| ip | inet | |
| expires_at | timestamptz | |
| revoked_at | timestamptz | nullable |
| created_at | timestamptz | |

---

## 2. Topologie

### `sites`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| name | text | |
| code | text UNIQUE | |
| address | text | |
| timezone | text | default `UTC` |
| metadata | jsonb | |
| archived_at | timestamptz | nullable |

### `zones`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| site_id | uuid FK sites | |
| name | text | |
| code | text | unique par site |
| sensitivity | enum(`low`,`medium`,`high`) | |
| active_hours | jsonb | ex: `{"mon":[["08:00","18:00"]]}` |
| metadata | jsonb | |
| archived_at | timestamptz | nullable |

Contrainte : `UNIQUE (site_id, code)`.

### `devices`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| site_id | uuid FK sites | |
| zone_id | uuid FK zones | nullable |
| name | text | |
| type | text | |
| model | text | |
| serial | text | |
| status | enum(`online`,`offline`,`maintenance`) | |
| last_seen_at | timestamptz | |

### `sensors`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| device_id | uuid FK devices | nullable |
| zone_id | uuid FK zones | |
| code | text UNIQUE | |
| type | enum(`motion`,`temperature`,`luminosity`,`door`,`presence`) | extensible |
| unit | text | |
| config | jsonb | seuils, calibration |
| status | enum(`online`,`offline`,`maintenance`) | |
| last_reading_at | timestamptz | |

### `sensor_readings`

> Haute volumétrie — partition mensuelle sur `recorded_at`.

| colonne | type | notes |
|---|---|---|
| id | uuid | |
| sensor_id | uuid FK sensors | |
| value | numeric | |
| recorded_at | timestamptz | |
| metadata | jsonb | |

PK composite `(sensor_id, recorded_at, id)`.

---

## 3. Événements

### `events`

> Haute volumétrie — partition mensuelle sur `occurred_at`.

| colonne | type | notes |
|---|---|---|
| id | uuid | |
| sensor_id | uuid FK sensors | nullable |
| zone_id | uuid FK zones | |
| site_id | uuid FK sites | |
| type | text | `motion`, `temperature_high`, … |
| severity | enum(`info`,`warning`,`critical`) | |
| value | numeric | nullable |
| occurred_at | timestamptz | |
| received_at | timestamptz | |
| source | enum(`sensor`,`simulator`,`external`,`manual`) | |
| idempotency_key | text | unique, nullable |
| payload | jsonb | brut normalisé |
| processed_at | timestamptz | nullable |
| created_at | timestamptz | |

Index :
- `(zone_id, occurred_at DESC)`
- `(type, occurred_at DESC)`
- `(site_id, occurred_at DESC)`
- `(idempotency_key)` unique where not null

### `event_metadata`

| colonne | type | notes |
|---|---|---|
| event_id | uuid FK events | PK composite |
| key | text | PK composite |
| value | text | |

---

## 4. Moteur de règles

### `rules`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| site_id | uuid FK sites | nullable — null = global |
| name | text | |
| description | text | |
| enabled | bool | default true |
| severity | enum(`info`,`warning`,`critical`) | |
| definition | jsonb | DSL conditions/actions |
| cooldown_seconds | int | anti-spam |
| created_by | uuid FK users | |
| archived_at | timestamptz | nullable |

### `rule_conditions`

> Dénormalisé pour indexation — reflète `definition.conditions`.

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| rule_id | uuid FK rules | |
| parent_id | uuid FK rule_conditions | nullable |
| operator | enum(`all`,`any`,`not`,`field`) | |
| field | text | nullable si operator ≠ field |
| op | text | nullable si operator ≠ field |
| value | jsonb | |
| order | int | |

### `rule_actions`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| rule_id | uuid FK rules | |
| type | enum(`create_alert`,`notify`,`tag_event`,`set_severity`) | |
| params | jsonb | |
| order | int | |

### `rule_executions`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| rule_id | uuid FK rules | |
| event_id | uuid FK events | |
| matched | bool | |
| duration_ms | int | |
| error | text | nullable |
| executed_at | timestamptz | |

Index `(rule_id, executed_at DESC)`, `(event_id)`.

---

## 5. Alertes & notifications

### `alerts`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| rule_id | uuid FK rules | nullable si manuelle |
| event_id | uuid FK events | nullable |
| zone_id | uuid FK zones | |
| site_id | uuid FK sites | |
| title | text | |
| description | text | |
| severity | enum(`info`,`warning`,`critical`) | |
| status | enum(`open`,`acknowledged`,`resolved`,`closed`,`false_positive`) | |
| assigned_to | uuid FK users | nullable |
| acknowledged_by | uuid FK users | nullable |
| acknowledged_at | timestamptz | |
| resolved_at | timestamptz | |
| closed_at | timestamptz | |
| dedup_key | text | regroupement |

Index `(status, severity, created_at DESC)`, `(site_id, created_at DESC)`, `(zone_id, created_at DESC)`.

### `alert_actions`

> Timeline de l'alerte.

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| alert_id | uuid FK alerts | |
| user_id | uuid FK users | nullable |
| action | enum(`created`,`acknowledged`,`assigned`,`commented`,`resolved`,`closed`,`reopened`) | |
| comment | text | |
| metadata | jsonb | |
| created_at | timestamptz | |

### `notifications`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| alert_id | uuid FK alerts | nullable |
| user_id | uuid FK users | |
| channel | enum(`email`,`web`,`webhook`) | |
| status | enum(`pending`,`sent`,`failed`) | |
| payload | jsonb | |
| sent_at | timestamptz | |
| error | text | nullable |

---

## 6. Analytics & anomalies

### `analyses`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| type | enum(`trend`,`volume`,`anomaly`,`custom`) | |
| scope | jsonb | site/zone/période |
| params | jsonb | |
| result | jsonb | |
| created_by | uuid FK users | |
| created_at | timestamptz | |

### `anomaly_scores`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| entity_type | enum(`zone`,`sensor`,`site`) | |
| entity_id | uuid | |
| window_start | timestamptz | |
| window_end | timestamptz | |
| score | numeric | |
| method | text | `zscore`, `iforest`, `composite` |
| features | jsonb | |
| created_at | timestamptz | |

Index `(entity_type, entity_id, window_start DESC)`.

---

## 7. IA

### `conversations`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK users | |
| title | text | |
| context | jsonb | site/zone/période |
| created_at | timestamptz | |
| archived_at | timestamptz | nullable |

### `messages`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| conversation_id | uuid FK conversations | |
| role | enum(`user`,`assistant`,`system`,`tool`) | |
| content | text | |
| tool_call_id | text | nullable |
| tokens_in | int | |
| tokens_out | int | |
| created_at | timestamptz | |

### `ai_tool_calls`

> Audit obligatoire.

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| message_id | uuid FK messages | |
| tool_name | text | |
| input | jsonb | |
| output | jsonb | nullable |
| status | enum(`ok`,`error`,`denied`) | |
| duration_ms | int | |
| error | text | nullable |
| created_at | timestamptz | |

Index `(tool_name, created_at DESC)`, `(message_id)`.

---

## 8. Rapports

### `reports`

| colonne | type | notes |
|---|---|---|
| id | uuid PK | |
| type | enum(`daily`,`weekly`,`custom`) | |
| scope | jsonb | |
| format | enum(`csv`,`json`,`pdf`) | |
| status | enum(`pending`,`generating`,`ready`,`failed`) | |
| file_path | text | nullable |
| params | jsonb | |
| created_by | uuid FK users | |
| created_at | timestamptz | |
| completed_at | timestamptz | nullable |

---

## 9. Audit

### `audit_logs`

> Append-only — partition mensuelle sur `created_at`.

| colonne | type | notes |
|---|---|---|
| id | uuid | |
| user_id | uuid FK users | nullable |
| action | text | |
| resource_type | text | |
| resource_id | uuid | nullable |
| ip | inet | |
| user_agent | text | |
| before | jsonb | nullable |
| after | jsonb | nullable |
| status | enum(`success`,`failure`) | |
| created_at | timestamptz | |

Index :
- `(user_id, created_at DESC)`
- `(resource_type, resource_id, created_at DESC)`
- `(action, created_at DESC)`

---

## 10. Paramètres

### `settings`

| colonne | type | notes |
|---|---|---|
| key | text | PK composite |
| scope | enum(`global`,`site`) | PK composite |
| site_id | uuid FK sites | PK composite, nullable si scope = global |
| value | jsonb | |
| updated_by | uuid FK users | |
| updated_at | timestamptz | |

---

## Récapitulatif des tables (23)

`users`, `roles`, `permissions`, `role_permissions`, `user_roles`,
`user_site_access`, `sessions`, `sites`, `zones`, `devices`, `sensors`,
`sensor_readings`, `events`, `event_metadata`, `rules`, `rule_conditions`,
`rule_actions`, `rule_executions`, `alerts`, `alert_actions`,
`notifications`, `analyses`, `anomaly_scores`, `conversations`, `messages`,
`ai_tool_calls`, `reports`, `audit_logs`, `settings`.
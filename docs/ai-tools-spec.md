# Sentinel — Spécification des outils IA

> Version 1.0 — Phase 0
> L'IA n'a aucun accès libre au système. Elle n'appelle que des outils
> explicitement autorisés, journalisés et soumis au RBAC.

## 1. Principe fondamental

Chaque outil possède :

- un **nom** unique
- un **schéma d'entrée** (Pydantic)
- un **schéma de sortie** (Pydantic)
- des **permissions requises** (héritées de l'utilisateur)
- des **limites** (volume, période, coût)
- une **journalisation obligatoire** dans `ai_tool_calls`

L'IA **ne peut pas** : écrire en base, modifier une règle, créer une alerte,
envoyer une notification, appeler un endpoint interne non listé.

---

## 2. Outils V1

### `query_events`

```python
Input:
  site_id: uuid | None
  zone_id: uuid | None
  types: list[str] | None
  severity: list[str] | None
  start: datetime
  end: datetime
  limit: int  # max 200

Output: list[EventSummary]  # pas de payload brut

Permission: event:read
Limite: période ≤ 30 jours, limit ≤ 200
```

### `get_zone_status`

```python
Input:
  zone_id: uuid

Output:
  zone: ZoneInfo
  sensors: list[SensorStatus]
  last_events: list[EventSummary]  # 10 derniers
  open_alerts: list[AlertSummary]
  anomaly_score: float | None

Permission: zone:read
```

### `get_alert`

```python
Input:
  alert_id: uuid

Output: AlertDetail  # avec timeline alert_actions

Permission: alert:read
```

### `summarize_period`

```python
Input:
  site_id: uuid | None
  zone_id: uuid | None
  start: datetime
  end: datetime

Output:
  event_count: int
  by_type: dict[str, int]
  by_severity: dict[str, int]
  alert_count: int
  anomaly_count: int
  highlights: list[str]  # calculé côté serveur

Permission: event:read
Limite: période ≤ 90 jours
```

### `compare_periods`

```python
Input:
  period_a: { start: datetime, end: datetime }
  period_b: { start: datetime, end: datetime }
  scope: { site_id?: uuid, zone_id?: uuid }

Output:
  deltas: dict[str, float]  # par métrique

Permission: event:read
```

### `explain_alert`

```python
Input:
  alert_id: uuid

Output:
  alert: AlertDetail
  triggering_event: EventSummary
  related_events: list[EventSummary]  # ±5 min autour
  rule: RuleInfo | None

Permission: alert:read
```

### `search_history` (V1.1)

```python
Input:
  query: str
  filters: dict
  limit: int

Output: list[EventSummary]

# recherche full-text PostgreSQL, pas vectorielle en V1
Permission: event:read
```

---

## 3. Ce que l'IA peut faire avec ces outils

- Expliquer une alerte → `explain_alert` + `query_events`
- Résumer une journée → `summarize_period`
- Comparer deux semaines → `compare_periods`
- Répondre « que s'est-il passé en zone A hier ? » → `query_events`
- Interpréter un score d'anomalie → `get_zone_status` + `query_events`

---

## 4. Ce que l'IA ne peut PAS faire

- Modifier une règle
- Créer ou fermer une alerte
- Envoyer une notification
- Exécuter une action physique
- Accéder aux données d'un site non autorisé
- Contourner le RBAC

Les outils héritent des permissions de l'utilisateur appelant.

---

## 5. Implémentation

- Chaque outil = une fonction Python décorée `@ai_tool`.
- Le décorateur : valide l'input, vérifie la permission, exécute, log
  dans `ai_tool_calls`.
- Le LLM reçoit la liste des outils au format function calling.
- Le provider LLM est abstrait derrière une interface `LLMProvider`.
- Sortie LLM structurée (Pydantic) quand c'est un rapport.

---

## 6. Journalisation obligatoire

Chaque appel écrit une ligne dans `ai_tool_calls` :

- `tool_name`
- `input`
- `output`
- `status` (`ok`, `error`, `denied`)
- `duration_ms`
- `error`
- `message_id`

C'est non négociable : sécurité, audit, debug.
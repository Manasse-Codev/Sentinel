# Sentinel — Spécification du moteur de règles

> Version 1.0 — Phase 0
> Le moteur est déterministe. Aucune IA n'intervient dans l'évaluation.

## 1. Principe

Le moteur évalue des règles contre chaque événement ingéré. Une règle =
un arbre de conditions + une liste d'actions. Si les conditions matchent,
les actions sont exécutées.

---

## 2. DSL (JSON)

```json
{
  "name": "Mouvement nocturne zone sensible",
  "severity": "critical",
  "cooldown_seconds": 300,
  "conditions": {
    "all": [
      { "field": "event.type", "op": "eq", "value": "motion" },
      { "field": "zone.sensitivity", "op": "eq", "value": "high" },
      { "field": "event.occurred_at", "op": "time_between", "value": ["22:00", "06:00"] },
      { "field": "zone.active_hours", "op": "outside", "value": true }
    ]
  },
  "actions": [
    { "type": "create_alert", "params": { "title": "Mouvement nocturne {zone.name}" } },
    { "type": "notify", "params": { "channels": ["web","email"], "roles": ["operator"] } }
  ]
}
```

---

## 3. Opérateurs supportés

### Logiques

- `all` — toutes les sous-conditions doivent être vraies
- `any` — au moins une
- `not` — négation

### Champs

- `eq`, `neq`
- `gt`, `gte`, `lt`, `lte`
- `in`, `not_in`
- `contains`
- `matches` (regex)
- `time_between` — plage horaire (`["22:00","06:00"]`)
- `outside` — hors plage
- `exists`

### Fenêtres temporelles (V1.1)

- `count_in_window` — N événements en T secondes
- `sequence` — A puis B dans T secondes
- `absence` — pas d'événement en T secondes

---

## 4. Champs disponibles dans le contexte

| namespace | champs |
|---|---|
| `event.*` | id, type, value, severity, occurred_at, source, payload.* |
| `sensor.*` | id, code, type, status, config.* |
| `zone.*` | id, name, code, sensitivity, active_hours |
| `site.*` | id, name, code, timezone |
| `history.*` | (V1.1) count_1h, count_24h, last_event_at |
| `anomaly.*` | (V1.1) score, method |

---

## 5. Actions supportées

| type | params | effet |
|---|---|---|
| `create_alert` | title, description, severity, assign_to_role | crée une alerte |
| `notify` | channels, roles/users | crée des notifications |
| `tag_event` | tags | ajoute des tags à l'événement |
| `set_severity` | severity | override la sévérité de l'événement |

---

## 6. Évaluation

1. Charger les règles `enabled` du site de l'événement + règles globales.
2. Trier par priorité (ordre de création en V1, extensible ensuite).
3. Pour chaque règle : évaluer l'arbre de conditions.
4. Si match : vérifier le cooldown — dédup via
   `dedup_key = rule_id + zone_id + bucket(temporel)`.
5. Exécuter les actions.
6. Enregistrer une ligne dans `rule_executions`.

---

## 7. Sécurité

- Validation stricte du DSL à la création/modification (Pydantic).
- Champs autorisés uniquement — whitelist stricte.
- Aucune évaluation de code arbitraire.
- Timeout 100 ms par règle.
- Limite 100 règles actives par site.
- Les actions `notify` respectent le RBAC (rôles destinataires valides).

---

## 8. Limites V1

- Pas de fenêtres temporelles (reporté V1.1).
- Pas de priorité entre règles (ordre de création).
- Pas de règles cross-site.
- Pas de règles basées sur `anomaly.*` (reporté V1.1).
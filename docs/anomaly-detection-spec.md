# Sentinel — Spécification détection d'anomalies

> Version 1.0 — Phase 0
> Deux méthodes simples, explicables, auditées. Pas de ML lourd en V1.

## 1. Principe

Combinaison de deux méthodes :

1. **Z-score sur fenêtres glissantes** — déviation vs historique récent.
2. **Isolation Forest** — combinaisons inhabituelles multivariées.

Score final composite normalisé `[0,1]`, stocké dans `anomaly_scores`.

---

## 2. Granularité

- Par **zone** (agrégat) — priorité V1.
- Par **capteur** — V1.1.
- Fenêtre : **1 heure**.

---

## 3. Features calculées par fenêtre (par zone)

| feature | description |
|---|---|
| `event_count` | nombre total d'événements |
| `event_count_by_type` | dict type → count |
| `alert_count` | nombre d'alertes générées |
| `unique_sensors` | nombre de capteurs ayant émis |
| `hour_of_day` | heure (cyclique) |
| `is_weekend` | booléen |
| `delta_vs_prev_hour` | variation vs heure précédente |
| `delta_vs_same_hour_7d` | variation vs même heure J-7 |

---

## 4. Méthode 1 — Z-score

Pour chaque feature scalaire :

```
z = (x - mean(window_30d, same_hour)) / std(window_30d, same_hour)
score_z = min(1, max(0, (|z| - 2) / 4))
```

- `score_z = 0` si `|z| < 2`
- `score_z = 1` si `|z| > 6`

Agrégation : moyenne pondérée des z-scores.

---

## 5. Méthode 2 — Isolation Forest

- Entraînement offline (job nocturne) sur 30 jours glissants.
- Features : vecteur normalisé des features de la section 3.
- `contamination = 0.05`.
- Score normalisé via `decision_function` → `[0,1]`.
- Modèle stocké dans `models/anomaly/{zone_id}.pkl`.
- Réentraînement quotidien si ≥ 1000 fenêtres disponibles.

---

## 6. Score composite

```
score_final = 0.4 * score_z + 0.6 * score_iforest
```

Seuils :

| plage | interprétation |
|---|---|
| `< 0.5` | normal |
| `0.5 – 0.75` | à surveiller |
| `0.75 – 0.9` | anomalie probable |
| `> 0.9` | anomalie critique |

Seuils configurables dans `settings`.

---

## 7. Déclenchement d'alerte

Une anomalie (`score > 0.75`) peut déclencher une alerte **via une règle** :

```json
{
  "conditions": {
    "all": [
      { "field": "anomaly.score", "op": "gt", "value": 0.75 },
      { "field": "zone.sensitivity", "op": "in", "value": ["medium","high"] }
    ]
  }
}
```

L'anomalie **ne crée jamais** d'alerte directement. Elle alimente le moteur
de règles, comme n'importe quel signal.

---

## 8. Explicabilité

Pour chaque anomalie, on stocke dans `features` :

- les features calculées
- les z-scores individuels
- la contribution de chaque feature au score

L'IA peut ensuite expliquer l'anomalie en langage naturel via
`get_zone_status`.

---

## 9. Jobs de calcul

| job | fréquence | rôle |
|---|---|---|
| Temps réel | à chaque événement | z-score léger |
| Batch horaire | toutes les heures | agrégation + IF sur l'heure complète |
| Batch quotidien | 1×/jour | réentraînement IF + recalcul 30j |

---

## 10. Limites V1

- Pas de détection par capteur individuel.
- Pas de deep learning.
- Pas de détection cross-zone.
- Cold start : 7 jours minimum avant que les scores soient fiables
  (affiché clairement dans l'UI).
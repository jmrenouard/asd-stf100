# Référence : Paramètres cluster, flux réseau, CLI et alertes

Spécifications techniques du composant `<nom-composant>` version `<version>`.

## 1. Paramètres de configuration

| Paramètre | Type | Défaut | Unité | Plage autorisée | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ttl` | entier | `30` | secondes | `10..300` | Durée du bail de leader dans le magasin de consensus. |
| `loop_wait` | entier | `10` | secondes | `2..60` | Intervalle de renouvellement du battement de cœur leader. |
| `retry_timeout` | entier | `10` | secondes | `3..60` | Délai d'expiration DCS avant rétrogradation du primaire. |
| `maximum_lag_on_failover` | entier | `1048576` | octets | `>= 0` | Retard maximal de réplication autorisé pour l'élection. |
| `synchronous_mode` | booléen | `false` | - | `true`, `false` | Active la validation synchrone sans perte de données. |

## 2. Matrice des ports et flux réseau

| Source | Destination | Protocole | Port | Direction | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Répartiteur applicatif | Nœuds primaire / secondaires | TCP | `5432` | Entrant | Connexions SQL lecture/écriture des clients. |
| Répartiteur applicatif | API REST Patroni | HTTP/HTTPS | `8008` | Entrant | Sondes de santé (`GET /primary`, `GET /replica`). |
| Nœuds base de données | Magasin de consensus (`etcd`) | TCP | `2379` | Sortant | Acquisition et renouvellement du bail de leader. |
| Magasin de consensus (`etcd`) | Pairs de consensus | TCP | `2380` | Bidirectionnel | Réplication du consensus Raft entre pairs. |
| Nœuds secondaires | Nœud primaire | TCP | `5432` | Bidirectionnel | Réplication en continu des journaux WAL. |

## 3. Options CLI et codes retour

### Options de `diataxis_check_fr.py`

| Option | Argument | Défaut | Comportement |
| :--- | :--- | :--- | :--- |
| `--strict` | aucun | `false` | Convertit chaque avertissement de gouvernance en échec bloquant. |
| `--check-stf` | aucun | `false` | Exécute `stf_check.py --mode procedural` sur `02-guides-pratiques/`. |

### Codes retour du processus

| Code retour | Constante | Signification |
| :--- | :--- | :--- |
| `0` | `EXIT_OK` | Validation terminée avec zéro erreur. |
| `1` | `EXIT_VALIDATION_ERROR` | Échec de structure, lien cassé, gouvernance ou contrôle STF. |
| `2` | `EXIT_USAGE_ERROR` | Option CLI invalide ou répertoire cible illisible. |

## 4. Matrice des alertes et codes d'erreur

| Alerte / Code | Gravité | Cause probable | Runbook de remédiation |
| :--- | :--- | :--- | :--- |
| `HA-001` (`LeaderLeaseLost`) | Critique | Magasin DCS inaccessible au-delà de `retry_timeout` ; primaire passé en lecture seule. | [Bascule manuelle du nœud primaire](../../02-guides-pratiques/gestion-incidents/bascule-primaire-manuelle.md) |
| `HA-002` (`ReplicationLagHigh`) | Avertissement | Application WAL retardée sur le nœud secondaire par saturation disque ou requête longue. | [Inspecter le retard de réplication](../../02-guides-pratiques/exploitation/inspecter-retard-replication.md) |
| `HA-003` (`SplitBrainRisk`) | Critique | Protection d'isolement déclenchée après partition réseau ; ancien leader bloqué. | [Reprise après isolement d'urgence](../../02-guides-pratiques/gestion-incidents/isolement-urgence.md) |

# Tutoriel : Déployer un bac à sable haute disponibilité local

> **Objectif pédagogique :** Déployer un cluster de test à 3 nœuds en local et observer une bascule automatique.
>
> **Avertissement d'environnement :** Exécutez cette leçon uniquement dans un bac à sable local Docker ou VM. N'exécutez jamais ces commandes sur un environnement de préproduction ou de production.

## Prérequis

Vérifiez que votre poste de travail dispose des éléments suivants :

- Docker Engine 24+ et Docker Compose v2 installés
- Minimum 4 Go de RAM libre et 5 Go d'espace disque disponible
- Ports locaux `5432`, `5433` et `8008` libres
- Terminal (`bash` ou `PowerShell`)

## Ce que vous allez construire

À la fin de ce tutoriel, vous aurez :

1. Démarré un cluster local à 3 nœuds dans des conteneurs Docker isolés.
2. Vérifié quel nœud détient actuellement le verrou de leader primaire.
3. Simulé la panne d'un nœud et observé l'élection automatique du nouveau leader.
4. Supprimé proprement tous les conteneurs et volumes de test.

## Étape 1 : Démarrer le bac à sable isolé

Créez un répertoire dédié au laboratoire et lancez la pile de conteneurs :

```bash
mkdir -p ~/diataxis-ha-lab && cd ~/diataxis-ha-lab
docker compose up -d
```

Résultat attendu :

```text
[+] Running 4/4
 ✔ Network diataxis-ha-lab_default  Created
 ✔ Container lab-etcd               Started
 ✔ Container lab-node-1             Started
 ✔ Container lab-node-2             Started
```

## Étape 2 : Inspecter l'état du cluster

Interrogez le plan de contrôle depuis le conteneur `lab-node-1` :

```bash
docker exec lab-node-1 patronictl -c /etc/patroni/patroni.yml list
```

Résultat attendu :

```text
+ Cluster: sandbox-ha (7310000000000000001) ---+-----------+----+-----------+
| Member     | Host       | Role    | State     | TL | Lag in MB |
+------------+------------+---------+-----------+----+-----------+
| lab-node-1 | 172.28.0.2 | Leader  | running   |  1 |           |
| lab-node-2 | 172.28.0.3 | Replica | streaming |  1 |         0 |
+------------+------------+---------+-----------+----+-----------+
```

Constatez que `lab-node-1` détient le rôle `Leader` pendant que `lab-node-2` réplique les données en flux continu.

## Étape 3 : Déclencher une bascule contrôlée

Arrêtez le conteneur leader actuel pour observer la réélection automatique :

```bash
docker stop lab-node-1
sleep 15
docker exec lab-node-2 patronictl -c /etc/patroni/patroni.yml list
```

Résultat attendu :

```text
+ Cluster: sandbox-ha (7310000000000000001) ---+-----------+----+-----------+
| Member     | Host       | Role    | State     | TL | Lag in MB |
+------------+------------+---------+-----------+----+-----------+
| lab-node-2 | 172.28.0.3 | Leader  | running   |  2 |           |
+------------+------------+---------+-----------+----+-----------+
```

Le nœud `lab-node-2` est maintenant `Leader` sur la timeline `2`.

## Étape 4 : Nettoyer l'environnement de laboratoire

Supprimez les conteneurs, réseaux et volumes temporaires :

```bash
docker compose down -v
```

Résultat attendu :

```text
[+] Running 4/4
 ✔ Container lab-node-2             Removed
 ✔ Container lab-node-1             Removed
 ✔ Container lab-etcd               Removed
 ✔ Network diataxis-ha-lab_default  Removed
```

## Prochaines étapes

- Exécuter une bascule planifiée en production : [Guides pratiques](../02-guides-pratiques/index.md)
- Consulter les paramètres, ports et seuils du cluster : [Référence](../03-reference/index.md)
- Comprendre les baux de consensus et la prévention du split-brain : [Explications](../04-explications/index.md)

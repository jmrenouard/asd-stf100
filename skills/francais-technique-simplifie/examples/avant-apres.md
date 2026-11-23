# Exemples avant / après en ASD-STF100

Ce document présente des transformations concrètes de textes techniques français vers **ASD-STF100**.
Tous les scénarios sont originaux et adaptés à l'exploitation logicielle, système et matérielle.

## Exemple 1 : Runbook de bascule sur incident

### Avant (non conforme)

> Avant de procéder au basculement manuel du cluster primaire, il conviendrait de
> s'assurer que le nœud secondaire est bien synchronisé et qu'aucune transaction
> d'écriture n'est éventuellement en cours ; dans le cas contraire, une corruption des
> données pourrait survenir lors de l'opération effectuée par l'administrateur.

### Après (conforme ASD-STF100)

> **ATTENTION :** Arrêtez le trafic d'écriture avant de lancer la bascule. Les transactions actives peuvent endommager la base de données.
>
> 1. Vérifiez que le nœud secondaire est synchronisé.
> 2. Si des écritures sont actives sur le nœud primaire, arrêtez le proxy applicatif.
> 3. Activez le nœud secondaire comme nouveau primaire.

### Pourquoi cette réécriture fonctionne

- Consigne `ATTENTION` avec commande directe puis énoncé exact du dommage matériel/données (Règles 7.1 à 7.3).
- Impératif direct sans `il conviendrait`, `éventuellement` ni `pourrait` (Règles 3.2 et 5.3).
- Aucune locution lourde (`procéder à`) ni passif avec `par` (Règles 3.6 et 3.7).
- Zéro point-virgule (Règle 8.1) et phrases de 20 mots ou moins (Règle 5.1).
- Condition placée avant la virgule (Règle 5.4).

---

## Exemple 2 : Texte descriptif d'architecture

### Avant (non conforme)

> Le collecteur de télémétrie agrège en continu les métriques issues des nœuds
> distribués qui sont supervisés par le plan de contrôle, lequel a été configuré
> afin de déclencher une alerte lorsque la latence disque dépasse 15 millisecondes, etc.

### Après (conforme ASD-STF100)

> Le collecteur reçoit les métriques de chaque nœud du cluster.
> Le plan de contrôle lit ces métriques toutes les 10 secondes.
> Si la latence disque dépasse 15 ms, le plan de contrôle envoie une alerte.
> Ainsi, l'équipe d'exploitation détecte le ralentissement avant la panne.

### Pourquoi cette réécriture fonctionne

- Une idée par phrase et 25 mots maximum en registre descriptif (Règles 6.1 et 6.3).
- Répétition assumée de `plan de contrôle` et `métriques` pour éviter l'ambiguïté (Règle 6.2).
- Suppression du passif avec `par`, de `afin de` et de l'abréviation latine `etc.` (Règles 3.6, 3.7, `GR-6`).
- `15 ms` et `10 secondes` comptés chacun comme un mot unique (Règle 8.6.2).

---

## Exemple 3 : Consigne de sécurité matérielle (`AVERTISSEMENT` vs `ATTENTION`)

### Avant (non conforme)

> Il faut faire très attention lors de l'intervention sur le boîtier d'alimentation du
> rack, car des bornes sous tension pourraient blesser le technicien ou détériorer
> les commutateurs réseau voisins.

### Après (conforme ASD-STF100)

> **AVERTISSEMENT :** Coupez l'alimentation du boîtier avant d'ouvrir le capot. Les bornes sous tension causent des blessures graves ou la mort.

### Pourquoi cette réécriture fonctionne

- Le risque corporel impose `AVERTISSEMENT` même si un risque matériel coexiste (Règle 7.1).
- La consigne commence par la commande de mise en sécurité (Règle 7.2) et précise le risque exact dans la phrase suivante (Règle 7.3).

---

## Exemple 4 : Liste verticale d'interdictions

### Avant (non conforme)

> Assurez-vous que les opérateurs ne contournent pas l'authentification, stockent des
> mots de passe en clair ou désactivent le journal d'audit pendant un déploiement.

### Après (conforme ASD-STF100)

> Pendant le déploiement en production :
>
> - Ne contournez pas l'authentification.
> - Ne stockez pas de mots de passe en clair.
> - Ne désactivez pas le journal d'audit.

### Pourquoi cette réécriture fonctionne

- Liste verticale introduite par deux-points (`:`) pour lever toute ambiguïté de portée (Règle 4.3).
- Répétition de la négation complète dans chaque élément de liste (Règle 4.3).

---

## Exemple 5 : Élimination des gérondifs et de la voix passive

### Avant (non conforme)

> En exécutant ce script, les fichiers temporaires seront automatiquement supprimés
> par le démon de nettoyage et les anciens journaux devraient disparaître.

### Après (conforme ASD-STF100)

> 1. Exécutez ce script.
> 2. Le démon de nettoyage supprime les fichiers temporaires.
> 3. Le démon supprime ensuite les anciens journaux.

### Pourquoi cette réécriture fonctionne

- Suppression du gérondif `En exécutant` (Règle 3.5), du passif avec `par` (Règle 3.6) et du modal interdit `devraient` (Règle 3.2).
- Chaque étape contient une action claire et vérifiable (Règle 5.2).

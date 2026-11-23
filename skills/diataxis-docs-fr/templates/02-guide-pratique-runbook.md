# Runbook : Bascule manuelle du nœud primaire

Consultez la [Matrice des alertes](../../03-reference/codes-erreurs/matrice-alertes.md)
avant de lancer cette procédure.

## Prérequis

- Disposez des droits d'administration sur le cluster.
- Vérifiez qu'un nœud secondaire est actif.
- Vérifiez que le retard de réplication reste inférieur à 10 Mo.
- Notez l'identifiant d'incident dans le journal d'exploitation.

## Consignes de sécurité

**ATTENTION :** Arrêtez le trafic d'écriture client avant la bascule.
Des écritures actives pendant l'opération endommagent les données.

## Étapes

1. Ouvrez une session SSH sur le serveur de gestion.
2. Vérifiez l'état actuel du cluster avec cette commande :

   ```bash
   patronictl -c /etc/patroni/patroni.yml list
   ```

3. Notez le nom du nœud primaire actif et du nœud secondaire cible.
4. Désactivez le trafic d'écriture sur le répartiteur applicatif.
5. Lancez la commande de bascule vers le nœud secondaire cible :

   ```bash
   patronictl -c /etc/patroni/patroni.yml switchover --leader <noeud-primaire> --candidate <noeud-secondaire>
   ```

6. Attendez 15 secondes que le cluster valide le changement de rôle.
7. Activez le trafic d'écriture sur le répartiteur applicatif.

## Vérification

1. Vérifiez le nouvel état du cluster avec cette commande :

   ```bash
   patronictl -c /etc/patroni/patroni.yml list
   ```

2. Vérifiez que le nœud cible affiche le rôle `Leader`.
3. Examinez le journal de la base pendant 60 secondes.
4. Vérifiez qu'aucune erreur n'apparaît dans le journal.

## Retour arrière

1. Si la vérification affiche une erreur, désactivez le trafic d'écriture client.
2. Examinez le journal du précédent nœud primaire.
3. Lancez la bascule vers le précédent nœud primaire :

   ```bash
   patronictl -c /etc/patroni/patroni.yml switchover --candidate <ancien-primaire>
   ```

4. Vérifiez l'état du cluster et le retard de réplication.
5. Activez le trafic d'écriture lorsque l'ancien primaire devient actif.

**NOTE :** Les répliques en lecture seule redémarrent automatiquement après le changement de leader.

## Documentation associée

- Référence des seuils : [Matrice des alertes](../../03-reference/codes-erreurs/matrice-alertes.md)
- Contexte technique : [Topologie haute disponibilité](../../04-explications/vue-architecture/topologie.md)

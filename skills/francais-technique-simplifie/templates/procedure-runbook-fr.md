---
title: <Titre de la procédure>
quadrant: 02-guides-pratiques
norme: ASD-STF100 Édition 1
---

# <Titre de la procédure>

Consultez la [Matrice des alertes](../../03-reference/codes-erreurs/matrice-alertes.md)
avant de démarrer cette intervention.

## Prérequis

- Disposez d'un accès administrateur sur le serveur `<HOTE_CIBLE>`.
- Sauvegardez le fichier de configuration `<CHEMIN_CONFIG>`.
- Vérifiez qu'aucune maintenance n'est active sur `<HOTE_SECONDAIRE>`.

## Consignes de sécurité

**AVERTISSEMENT :** Coupez l'alimentation du châssis avant d'ouvrir le capot.
La tension électrique cause des blessures graves ou la mort.

**ATTENTION :** Sauvegardez la base de données avant d'arrêter le service.
Un arrêt sans sauvegarde endommage les données actives.

## Étapes

1. Ouvrez une session SSH sur le serveur `<HOTE_CIBLE>`.
2. Vérifiez l'état du service avec cette commande :

   ```bash
   <COMMANDE_ETAT>
   ```

3. Si des sessions client sont actives, fermez ces connexions sur `<REPARTITEUR>`.
4. Arrêtez le service cible avec cette commande :

   ```bash
   <COMMANDE_ARRET>
   ```

5. Appliquez le nouveau paramètre dans le fichier `<CHEMIN_CONFIG>`.
6. Démarrez le service cible avec cette commande :

   ```bash
   <COMMANDE_DEMARRAGE>
   ```

**NOTE :** Le service termine son démarrage en 15 secondes ou moins après `<COMMANDE_DEMARRAGE>`.

## Vérification

1. Exécutez la commande de vérification sur `<HOTE_CIBLE>` :

   ```bash
   <COMMANDE_SANTE>
   ```

2. Vérifiez que la sortie affiche l'état `ACTIF`.
3. Examinez le journal système `<CHEMIN_JOURNAL>` pour détecter toute erreur.
4. Si le journal n'indique aucune erreur, activez le trafic sur `<REPARTITEUR>`.

## Retour arrière

1. Si la vérification affiche une erreur, arrêtez le service cible.
2. Remplacez le fichier `<CHEMIN_CONFIG>` par la sauvegarde `<CHEMIN_SAUVEGARDE>`.
3. Démarrez le service cible avec la commande `<COMMANDE_DEMARRAGE>`.
4. Vérifiez que le service répond sans erreur.

## Documentation associée

- Architecture et contexte : [Vue d'architecture](../../04-explications/vue-architecture/index.md)

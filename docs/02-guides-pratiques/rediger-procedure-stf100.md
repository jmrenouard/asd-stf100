# Rédiger une procédure en ASD-STF100

Consultez les [Règles de rédaction](../03-reference/regles-redaction.md)
et le [Dictionnaire STF-100](../03-reference/dictionnaire-stf.md).

## Prérequis

- Installez le paquet `asd-stf100` dans votre environnement Python.
- Identifiez l'objectif exact de la procédure.
- Vérifiez que le document appartient au dossier `02-guides-pratiques/`.

## Consignes de sécurité

**ATTENTION :** Sauvegardez le fichier source avant toute réécriture.
Une suppression directe entraîne une perte de contenu.

## Étapes

1. Copiez le fichier source vers un brouillon de sauvegarde.
2. Séparez les explications théoriques vers le dossier `04-explications/`.
3. Placez chaque tableau de paramètres dans le dossier `03-reference/`.
4. Rédigez chaque titre d'étape avec un verbe à l'infinitif ou à l'impératif.
5. Écrivez chaque instruction à la voix active et à l'impératif direct.
6. Limitez chaque phrase procédurale à 20 mots ou moins.
7. Exprimez une seule action par phrase.
8. Si une condition déclenche une action, placez la condition avant la virgule.
9. Supprimez tous les points-virgules et divisez ces phrases en deux.
10. Remplacez les modaux incertains par des verbes d'action directs.
11. Gardez le même terme technique français pour chaque élément.
12. Ajoutez une section de vérification et une section de retour arrière.

**NOTE :** Le texte descriptif et les notes acceptent jusqu'à 25 mots par phrase.

## Vérification

1. Exécutez le linter STF en mode procédural sur le fichier rédigé :

   ```bash
   python -m asd_stf100.stf_check --mode procedural docs/02-guides-pratiques/<fichier>.md
   ```

2. Vérifiez que le résultat affiche zéro erreur bloquante.
3. Si une erreur apparaît, corrigez la ligne signalée et exécutez de nouveau la commande.

## Retour arrière

1. Si la réécriture casse le sens technique, restaurez le brouillon de sauvegarde :

   ```bash
   cp <fichier>.bak docs/02-guides-pratiques/<fichier>.md
   ```

2. Exécutez de nouveau le linter après la restauration du fichier initial.

## Documentation associée

- Règles complètes : [Règles de rédaction](../03-reference/regles-redaction.md)
- Fondements de la norme : [Principes fondamentaux d'ASD-STF100](../04-explications/principes-asd-stf100.md)

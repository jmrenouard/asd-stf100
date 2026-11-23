# Migrer une documentation vers Diátaxis

Consultez la [Matrice Diátaxis (FR)](../03-reference/matrice-diataxis-fr.md) avant de classer vos documents.

## Prérequis

- Créez une copie de travail Git dédiée avant de déplacer des fichiers.
- Inventoriez tous les fichiers Markdown du dépôt cible.
- Installez `asd-stf100` dans votre environnement Python local.

## Consignes de sécurité

**ATTENTION :** Gardez les anciens fichiers jusqu'à la validation des nouveaux liens.
Une suppression prématurée casse la navigation du portail documentaire.

## Étapes

1. Créez l'arborescence Diátaxis dans le projet cible avec `diataxis-fr-scaffold` :

   ```bash
   diataxis-fr-scaffold <repertoire_cible> --profile infra --with-ci
   ```

2. Analysez chaque document source et séparez ses sections par type.
3. Déplacez les leçons d'apprentissage isolées vers `docs/01-tutoriels/`.
4. Réécrivez les procédures d'exploitation en **ASD-STF100** dans `docs/02-guides-pratiques/`.
5. Extrayez les tableaux de paramètres et codes d'erreur vers `docs/03-reference/`.
6. Déplacez les schémas d'architecture et dossiers ADR vers `docs/04-explications/`.
7. Reliez les quatre sections avec des liens relatifs propres.
8. Mettez à jour les entrées `nav:` dans le fichier `mkdocs.yml`.

## Vérification

1. Exécutez le validateur Diátaxis FR avec vérification STF active :

   ```bash
   python -m asd_stf100.diataxis_check_fr docs --strict --check-stf
   ```

2. Vérifiez que le résumé final affiche zéro erreur et zéro avertissement.

## Retour arrière

1. Si la migration génère des liens cassés, supprimez la copie de travail :

   ```bash
   git checkout main
   git branch -D <branche_migration>
   ```

2. Corrigez les cibles manquantes avant de lancer une nouvelle migration.

## Documentation associée

- Grille de classement : [Matrice Diátaxis (FR)](../03-reference/matrice-diataxis-fr.md)
- Guide complet : [Guide Diátaxis et Docs-as-Code](../04-explications/methodologie-diataxis-et-docs-as-code.md)

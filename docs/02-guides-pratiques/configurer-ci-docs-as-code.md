# Configurer la CI Docs-as-Code

Consultez les [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md) pour les options des outils.

## Prérequis

- Disposez des droits d'écriture sur le dépôt Git cible.
- Vérifiez la présence de `docs/index.md` et des quatre dossiers.
- Installez `asd-stf100` pour tester les scripts en local.

## Consignes de sécurité

**ATTENTION :** Testez la configuration Docs-as-Code localement avant de pousser vers `main`.
Une règle mal écrite bloque toutes les Pull Requests documentaires.

## Étapes

1. Générez les fichiers de configuration racine avec l'option `--with-ci` :

   ```bash
   diataxis-fr-scaffold . --profile infra --with-ci
   ```

2. Ouvrez `mkdocs.yml` et listez toutes vos pages dans la section `nav:`.
3. Vérifiez les quatre fichiers de règles sous `.vale/styles/STF100/`.
4. Vérifiez que `.vale.ini` cible le dossier `docs/02-guides-pratiques/**/*.md`.
5. Vérifiez les paramètres de ligne et de tableaux dans `.markdownlint.json`.
6. Examinez le déclenchement sur `main` dans `.github/workflows/docs-ci.yml`.
7. Validez la documentation localement avant de créer votre commit.

## Vérification

1. Lancez la validation complète en mode strict :

   ```bash
   python -m asd_stf100.diataxis_check_fr docs --strict --check-stf
   ```

2. Si `mkdocs` est installé, compilez le site en mode strict :

   ```bash
   mkdocs build --strict
   ```

3. Vérifiez que chaque commande termine avec le code retour `0`.

## Retour arrière

1. Si la chaîne CI échoue après fusion, restaurez les configurations :

   ```bash
   git revert <commit_ci>
   ```

2. Corrigez la configuration en local avant une nouvelle Pull Request.

## Documentation associée

- Paramètres CLI : [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md)
- Architecture CI : [Guide Diátaxis et Docs-as-Code](../04-explications/methodologie-diataxis-et-docs-as-code.md)

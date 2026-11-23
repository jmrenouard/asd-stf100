# Tutoriel : Initialiser une documentation Diátaxis FR

> **Objectif pédagogique :** Générer une arborescence documentaire française complète avec
> `diataxis-fr-scaffold`, ajouter un runbook conforme et valider avec `diataxis-fr-check`.
>
> **Avertissement d'environnement :** Travaillez dans un dossier temporaire vide
> pour éviter de modifier un dépôt existant.

## Prérequis

Vérifiez la présence de ces éléments :

- Le paquet `asd-stf100` installé (`pip install -e .`)
- Un répertoire de travail vide (`~/demo-diataxis-fr`)

## Ce que vous allez réaliser

À la fin de cette leçon, vous aurez :

1. Généré l'arborescence Diátaxis FR (`infra`) et ses fichiers Docs-as-Code.
2. Créé un runbook minimal dans `docs/02-guides-pratiques/exploitation/`.
3. Exécuté la validation complète `--strict --check-stf`.

## Étape 1 : Prévisualiser puis générer l'arborescence

Prévisualisez d'abord les opérations sans écrire sur le disque grâce à `--dry-run` :

```bash
mkdir -p ~/demo-diataxis-fr
diataxis-fr-scaffold ~/demo-diataxis-fr --profile infra --with-ci --dry-run
```

Résultat attendu :

```text
[DRY-RUN CREATE DIR] .../demo-diataxis-fr/docs
...
[DRY-RUN WRITE] .../demo-diataxis-fr/mkdocs.yml
[DRY-RUN WRITE] .../demo-diataxis-fr/.vale/styles/STF100/ModauxInterdits.yml
```

Exécutez ensuite la création réelle :

```bash
diataxis-fr-scaffold ~/demo-diataxis-fr --profile infra --with-ci
```

## Étape 2 : Ajouter un runbook dans `02-guides-pratiques/`

Créez le fichier `~/demo-diataxis-fr/docs/02-guides-pratiques/exploitation/verifier-service.md` :

```markdown
# Vérifier le service applicatif

Consultez la [Référence](../../03-reference/index.md) avant toute intervention.

## Prérequis

- Disposez d'un accès administrateur sur le serveur cible.

## Étapes

1. Ouvrez une session SSH sur le serveur cible.
2. Exécutez la commande `systemctl status mon-service`.

## Vérification

1. Vérifiez que l'état affiché indique `active (running)`.

## Retour arrière

1. Si le service échoue, exécutez `systemctl restart mon-service`.
```

## Étape 3 : Valider la structure, les liens et le style STF

Lancez le validateur en mode strict avec contrôle ASD-STF100 :

```bash
diataxis-fr-check ~/demo-diataxis-fr/docs --strict --check-stf
```

Résultat attendu :

```text
Summary: 0 error(s), 0 warning(s) across 6 markdown file(s).
```

## Étape 4 : Supprimer le bac à sable

Supprimez le dossier de démonstration lorsque vous avez terminé :

```bash
rm -rf ~/demo-diataxis-fr
```

## Prochaines étapes

- Configurer la CI : [Configurer la CI Docs-as-Code](../02-guides-pratiques/configurer-ci-docs-as-code.md)
- Consulter les options CLI : [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md)
- Comprendre les 4 quadrants :
  [Méthodologie Diátaxis et Docs-as-Code](../04-explications/methodologie-diataxis-et-docs-as-code.md)

# Référence : Commandes CLI et codes retour

Spécification des outils en ligne de commande fournis par le paquet `asd-stf100` et les scripts du dépôt.

## 1. Linter linguistique (`stf-check` / `asd_stf100.stf_check`)

```text
stf-check [--mode procedural|descriptive|mixed] [--dict PATH] [--no-vocab] [FILES...]
```

| Option / Argument | Valeur par défaut | Comportement |
| :--- | :--- | :--- |
| `FILES...` | `stdin` | Fichiers Markdown ou texte à analyser. Lit l'entrée standard si aucun fichier n'est fourni. |
| `--mode` | `mixed` | `procedural` impose `<= 20` mots/phrase ; `descriptive` impose `<= 25` ; `mixed` applique les règles mixtes. |
| `--dict PATH` | `spec/dictionary.json` (ou `../references/dictionnaire-stf.md`) | Chemin vers un dictionnaire contrôlé alternatif. |
| `--no-vocab` | `false` | Désactive la vérification lexicale et conserve uniquement les contrôles structurels et stylistiques. |

## 2. Générateur d'arborescence (`diataxis-fr-scaffold` / `asd_stf100.scaffold_diataxis_fr`)

```text
diataxis-fr-scaffold <target_dir> [--profile infra|logiciel] [--with-ci] [--dry-run] [--force]
```

| Option / Argument | Valeur par défaut | Comportement |
| :--- | :--- | :--- |
| `target_dir` | obligatoire | Racine du projet où créer `docs/` et les fichiers racine optionnels. |
| `--profile` | `infra` | `infra` crée les sous-répertoires métier ; `logiciel` crée uniquement les 4 quadrants et `assets/`. |
| `--with-ci` | `false` | Écrit `mkdocs.yml`, `.vale.ini`, `.vale/styles/STF100/*.yml`, `.markdownlint.json` et `.github/workflows/docs-ci.yml`. |
| `--dry-run` | `false` | Affiche les opérations planifiées sans modifier le disque. |
| `--force` | `false` | Autorise le remplacement des fichiers déjà présents sur le disque. |

## 3. Validateur Diátaxis FR (`diataxis-fr-check` / `asd_stf100.diataxis_check_fr`)

```text
diataxis-fr-check <docs_dir> [--strict] [--check-stf]
```

| Option / Argument | Valeur par défaut | Comportement |
| :--- | :--- | :--- |
| `docs_dir` | obligatoire | Chemin vers le dossier `docs/` à auditer. |
| `--strict` | `false` | Convertit chaque avertissement de gouvernance (`WARN`) en erreur bloquante (`ERROR`). |
| `--check-stf` | `false` | Exécute `stf_check.py --mode procedural` sur tous les fichiers non-index de `02-guides-pratiques/`. |

## 4. Scripts de synchronisation et de génération PDF

| Script | Options | Rôle |
| :--- | :--- | :--- |
| `scripts/sync_docs.py` | `[--check]` | Régénère `docs/03-reference/{regles-redaction,dictionnaire-stf,categories-techniques}.md`, `skills/francais-technique-simplifie/references/*` et copie `stf_check.py`. Avec `--check`, échoue (`1`) si un fichier diverge. |
| `scripts/build_pdf.py` | `[--output PATH]` | Compile la spécification PDF complète (par défaut `dist/ASD-STF100_ISSUE1.pdf`) à partir de `spec/*.json`. |

## 5. Codes retour communs

| Code retour | Signification | Action recommandée |
| :--- | :--- | :--- |
| `0` | Succès complet (aucune erreur bloquante) | Poursuivre le commit ou le pipeline CI. |
| `1` | Erreur détectée (règle STF, lien cassé, structure, désynchronisation ou `--strict`) | Corriger les diagnostics affichés avant validation. |
| `2` | Erreur d'arguments CLI (`argparse`) | Vérifier la syntaxe des options avec `--help`. |

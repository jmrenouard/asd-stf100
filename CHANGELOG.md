# Changelog

Toutes les évolutions notables de **ASD-STF100** sont documentées dans ce fichier.
Le format s'appuie sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le versionnement sémantique.

## [1.0.0] — 2026-11-23

### Ajouté

- **Spécification ASD-STF100 Édition 1 (`spec/*.json`) :**
  - 53 règles françaises de rédaction technique contrôlée (Sections 1 à 9) et 8 recommandations générales (`GR-1` à `GR-8`).
  - 22 catégories de noms techniques et 4 catégories de verbes techniques.
  - Dictionnaire contrôlé français (`>= 450` entrées approuvées, `>= 150` termes non approuvés avec alternatives, `>= 40` erreurs récurrentes).
- **Linter Python `asd_stf100.stf_check` (`stf-check`) :**
  - Analyse sans dépendance externe des limites de phrases, paragraphes, points-virgules, modaux interdits, voix passive avec `par`, gérondifs, locutions lourdes, abréviations latines et lexique.
  - Masquage du frontmatter YAML, des blocs/spans de code, des URL, des citations et des formules mathématiques LaTeX (`$...$`, `$$...$$`).
- **Boîte à outils Diátaxis (FR) et Docs-as-Code :**
  - `asd_stf100.scaffold_diataxis_fr` (`diataxis-fr-scaffold`) avec profils `infra` et `logiciel`, `--with-ci`, `--dry-run`, `--force`.
  - `asd_stf100.diataxis_check_fr` (`diataxis-fr-check`) avec vérification de structure, liens relatifs, garde-fous par quadrant (`--strict`) et chaînage `stf_check.py` (`--check-stf`).
  - Configuration Docs-as-Code complète : `mkdocs.yml`, `.vale.ini`, `.vale/styles/STF100/*.yml`, `.markdownlint.json`, `.github/workflows/docs-ci.yml`.
- **Documentation complète du dépôt (`docs/`)** structurée selon les 4 quadrants Diátaxis (FR) et synchronisée par `scripts/sync_docs.py`.
- **Agent Skills installables (`skills/`) :** `francais-technique-simplifie` et `diataxis-docs-fr`.
- **Spécification PDF (`dist/ASD-STF100_ISSUE1.pdf`)** générée par `scripts/build_pdf.py` (ReportLab A4) et validée par CI.

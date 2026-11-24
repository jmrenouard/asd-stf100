# ASD-STF100 — Français Technique Simplifié

**Norme ouverte de rédaction technique contrôlée en français, linter Python sans dépendance, spécification PDF et boîte à outils Diátaxis (FR) / Docs-as-Code.**

> **English Summary:** `ASD-STF100` (*Français Technique Simplifié*) is an independent, open-source controlled French technical writing specification (53 rules, 8 general recommendations, 22 technical noun categories, 4 technical verb categories, controlled dictionary), paired with a zero-dependency Python linter (`stf-check`), a French Diátaxis Docs-as-Code toolkit (`diataxis-fr-scaffold`, `diataxis-fr-check`), a ReportLab A4 specification PDF (`dist/ASD-STF100_ISSUE1.pdf`), and installable Agent Skills (`skills/`).

> **Avis de non-affiliation :** `ASD-STF100` est un projet open-source indépendant inspiré sur le plan méthodologique par `ASD-STE100` (Issue 9, 2025-01-15). Il n'est ni affilié, ni parrainé, ni approuvé, ni certifié par l'ASD (*Aerospace, Security and Defence Industries Association of Europe*) ni par le *STE Maintenance Group* (STEMG). `ASD-STE100` est une marque enregistrée de l'Union européenne appartenant à l'ASD (**EU Trade Mark No. 017966390** ; enregistrement antérieur n° 004901195). Ce projet ne reproduit ni les définitions ni les exemples officiels d'`ASD-STE100`. Voir [`NOTICE.md`](NOTICE.md).

---

## Fonctionnalités principales

- **Spécification normative structurée (`spec/*.json`) :**
  - **53 règles françaises** réparties en 9 sections (`1.1`–`9.4`) et **8 recommandations générales** (`GR-1`–`GR-8`).
  - **22 catégories de noms techniques** et **4 catégories de verbes techniques**.
  - **Dictionnaire contrôlé français** (`>= 450` entrées approuvées, `>= 150` termes déconseillés avec alternatives et exemples originaux, `>= 40` erreurs récurrentes).
- **Linter Python autonome (`stf-check`) :**
  - Zéro dépendance externe (bibliothèque standard Python `3.10+` uniquement).
  - Masquage automatique des blocs de code, liens Markdown, chaînes citées et formules mathématiques LaTeX (`$...$`, `$$...$$`).
  - Modes `--mode procedural|descriptive|mixed`, contrôle des modaux interdits (`devrait`, `pourrait`, `serait`, `éventuellement`), de la voix passive avec `par`, du point-virgule, des locutions lourdes et du lexique.
- **Boîte à outils Diátaxis (FR) & Docs-as-Code :**
  - `diataxis-fr-scaffold` : création d'arborescence `docs/` (`infra` ou `logiciel`) et configuration complète `--with-ci` (`mkdocs.yml`, `.vale.ini`, `.vale/styles/STF100/*.yml`, `.markdownlint.json`, `.github/workflows/docs-ci.yml`).
  - `diataxis-fr-check` : audit de structure, liens relatifs, heuristiques des 4 quadrants (`--strict`) et exécution chaînée de `stf_check.py` (`--check-stf`) sur `docs/02-guides-pratiques/`.
- **Spécification PDF publiable :** [`dist/ASD-STF100_ISSUE1.pdf`](dist/ASD-STF100_ISSUE1.pdf) générée par ReportLab depuis la source unique `spec/*.json`.
- **Agent Skills installables (`skills/`) :** `francais-technique-simplifie` et `diataxis-docs-fr`, prêts à être copiés dans tout workspace ou répertoire de skills IA.

---

## Installation et démarrage rapide

```bash
git clone https://github.com/jmrenouard/asd-stf100.git
cd asd-stf100
python -m venv .venv
# Linux / macOS :
source .venv/bin/activate
# Windows PowerShell :
# .\.venv\Scripts\Activate.ps1

pip install -e ".[pdf,dev]"
```

### Exécuter le linter ASD-STF100

```bash
# Analyser un guide pratique en mode procédural strict (<= 20 mots/phrase)
stf-check --mode procedural docs/02-guides-pratiques/rediger-procedure-stf100.md

# Analyser sans vérification du dictionnaire
stf-check --mode mixed --no-vocab mon-document.md
```

### Initialiser et valider une documentation Diátaxis FR

```bash
# Générer une arborescence Diátaxis complète + CI Docs-as-Code
diataxis-fr-scaffold ./mon-projet --profile infra --with-ci

# Auditer structure, liens, gouvernance et conformité ASD-STF100
diataxis-fr-check docs --strict --check-stf
```

---

## Carte de la documentation (`docs/`)

La documentation du dépôt applique elle-même **Diátaxis (FR)** et **ASD-STF100** :

| Quadrant | Répertoire | Contenu principal |
| :--- | :--- | :--- |
| **Portail** | [`docs/index.md`](docs/index.md) | Présentation et points d'entrée |
| **1. Tutoriels** | [`docs/01-tutoriels/`](docs/01-tutoriels/index.md) | Démarrage rapide `stf-check` et initialisation Diátaxis FR |
| **2. Guides pratiques** | [`docs/02-guides-pratiques/`](docs/02-guides-pratiques/index.md) | Procédures opérationnelles validées par `stf-check --mode procedural` |
| **3. Référence** | [`docs/03-reference/`](docs/03-reference/index.md) | 53 règles, dictionnaire STF, catégories, matrice Diátaxis et CLI |
| **4. Explications** | [`docs/04-explications/`](docs/04-explications/index.md) | Principes ASD-STF100, méthodologie Diátaxis/Docs-as-Code et ADR-001 |

---

## Installation des Agent Skills

Deux skills autonomes sont fournis dans [`skills/`](skills/) :

1. **`skills/francais-technique-simplifie/`** : rédaction et audit de procédures françaises en ASD-STF100 (inclut `SKILL.md`, `references/`, `examples/avant-apres.md`, `templates/procedure-runbook-fr.md`, `scripts/stf_check.py`).
2. **`skills/diataxis-docs-fr/`** : architecture documentaire Diátaxis (FR) et chaîne Docs-as-Code (inclut `SKILL.md`, `references/`, `templates/`, `scripts/scaffold_diataxis_fr.py`, `scripts/diataxis_check_fr.py`).

Copiez ces deux dossiers dans votre répertoire global de skills (par exemple `~/.gemini/config/skills/` ou `.github/skills/`) pour les activer dans vos projets.

---

## Chaîne Docs-as-Code et génération PDF

- **Synchroniser les fichiers générés depuis `spec/*.json` :** `python scripts/sync_docs.py` (vérification en CI : `python scripts/sync_docs.py --check`).
- **Compiler la norme PDF :** `python scripts/build_pdf.py --output dist/ASD-STF100_ISSUE1.pdf`.
- **Exécuter la suite de tests complète :** `pytest -v`.
- **Pipeline CI :** `.github/workflows/ci.yml` (tests, synchronisation, Diátaxis + STF, build PDF), `.github/workflows/docs-ci.yml` (validation documentaire, markdownlint, Vale `STF100`, `mkdocs build --strict`) et `.github/workflows/docs-publish.yml` (compilation et publication MkDocs versionnée sur IONOS).

---

## Contribution et licences

Consultez [`CONTRIBUTING.md`](CONTRIBUTING.md) pour le flux GitHub et les conventions linguistiques, et [`CHANGELOG.md`](CHANGELOG.md) pour l'historique des versions.

- **Code Python, scripts, outils CLI, tests et Agent Skills** (`src/`, `scripts/`, `tests/`, `skills/`) : licence **MIT** ([`LICENSE`](LICENSE)).
- **Spécification, règles, dictionnaire, documentation et PDF** (`spec/*.json`, `docs/`, `dist/ASD-STF100_ISSUE1.pdf`) : licence **CC-BY-SA-4.0** ([`NOTICE.md`](NOTICE.md)).

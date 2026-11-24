#!/usr/bin/env python3
"""Scaffold a French Diataxis documentation tree and Docs-as-Code toolchain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

INFRA_DIRS = [
    "docs",
    "docs/assets",
    "docs/assets/architecture",
    "docs/assets/runbooks",
    "docs/01-tutoriels",
    "docs/02-guides-pratiques",
    "docs/02-guides-pratiques/deploiement",
    "docs/02-guides-pratiques/exploitation",
    "docs/02-guides-pratiques/gestion-incidents",
    "docs/02-guides-pratiques/securite",
    "docs/03-reference",
    "docs/03-reference/architecture-specs",
    "docs/03-reference/configuration",
    "docs/03-reference/cli-et-scripts",
    "docs/03-reference/codes-erreurs",
    "docs/04-explications",
    "docs/04-explications/vue-architecture",
    "docs/04-explications/decisions-architecture",
    "docs/04-explications/analyses-internes",
]

LOGICIEL_DIRS = [
    "docs",
    "docs/assets",
    "docs/assets/architecture",
    "docs/assets/runbooks",
    "docs/01-tutoriels",
    "docs/02-guides-pratiques",
    "docs/03-reference",
    "docs/04-explications",
]

ROOT_INDEX_MD = """# Documentation technique

Bienvenue sur le portail documentaire structuré selon la méthodologie **Diátaxis**.

## Les quatre quadrants

| Quadrant | Objectif | Point d'entrée |
| :--- | :--- | :--- |
| **Tutoriels** | Leçons guidées en environnement isolé pour apprendre | [01-tutoriels](01-tutoriels/index.md) |
| **Guides pratiques** | Procédures et runbooks orientés action (ASD-STF100) | [02-guides-pratiques](02-guides-pratiques/index.md) |
| **Référence** | Spécifications neutres, paramètres CLI et codes d'erreur | [03-reference](03-reference/index.md) |
| **Explications** | Architecture, compromis techniques et dossiers ADR | [04-explications](04-explications/index.md) |
"""

TUTORIELS_INDEX_MD = """# Tutoriels

Leçons pratiques orientées apprentissage dans un environnement local isolé et reproductible.

- Retour vers [l'accueil de la documentation](../index.md)
- Passer aux tâches d'exploitation : [Guides pratiques](../02-guides-pratiques/index.md)
"""

GUIDES_INDEX_MD = """# Guides pratiques et runbooks

Procédures opérationnelles orientées objectif rédigées en **ASD-STF100** (Français Technique Simplifié).

## Domaines

- `deploiement/` — Procédures d'installation, de migration et de mise à niveau
- `exploitation/` — Tâches courantes de maintenance et d'administration
- `gestion-incidents/` — Runbooks d'astreinte et de reprise sur incident
- `securite/` — Rotation des secrets, durcissement et audits

## Quadrants associés

- Seuils d'alerte et paramètres : [Référence](../03-reference/index.md)
- Topologie système et décisions : [Explications](../04-explications/index.md)
- Portail documentaire : [Accueil](../index.md)
"""

REFERENCE_INDEX_MD = """# Référence

Spécifications techniques factuelles, neutres et exhaustives.

## Domaines

- `architecture-specs/` — Dimensionnement, accords de service et flux réseau
- `configuration/` — Paramètres, types, valeurs par défaut et unités
- `cli-et-scripts/` — Options de commande, variables et codes retour
- `codes-erreurs/` — Matrices d'alertes, causes probables et renvois runbooks

## Quadrants associés

- Procédures opérationnelles : [Guides pratiques](../02-guides-pratiques/index.md)
- Contexte d'architecture et ADR : [Explications](../04-explications/index.md)
- Portail documentaire : [Accueil](../index.md)
"""

EXPLICATIONS_INDEX_MD = """# Explications

Vues d'architecture, analyses de compromis et dossiers de décisions d'architecture (ADR).

## Domaines

- `vue-architecture/` — Topologie générale et flux de données
- `decisions-architecture/` — Architecture Decision Records (ADR)
- `analyses-internes/` — Mécanismes internes et retours d'expérience

## Quadrants associés

- Valeurs exactes et paramètres : [Référence](../03-reference/index.md)
- Procédures exécutables : [Guides pratiques](../02-guides-pratiques/index.md)
- Portail documentaire : [Accueil](../index.md)
"""

INDEX_FILES: dict[str, str] = {
    "docs/index.md": ROOT_INDEX_MD,
    "docs/01-tutoriels/index.md": TUTORIELS_INDEX_MD,
    "docs/02-guides-pratiques/index.md": GUIDES_INDEX_MD,
    "docs/03-reference/index.md": REFERENCE_INDEX_MD,
    "docs/04-explications/index.md": EXPLICATIONS_INDEX_MD,
}

DEFAULT_MKDOCS_YML = """site_name: Documentation Technique
site_description: Documentation d'architecture et d'exploitation structurée avec Diátaxis (FR)
docs_dir: docs

theme:
  name: material
  language: fr
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.indexes
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
  palette:
    - scheme: default
      primary: indigo
      accent: cyan
      toggle:
        icon: material/brightness-7
        name: Passer au mode sombre
    - scheme: slate
      primary: indigo
      accent: cyan
      toggle:
        icon: material/brightness-4
        name: Passer au mode clair

markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - footnotes
  - tables
  - toc:
      permalink: true
  - pymdownx.details
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true

nav:
  - Accueil: index.md
  - Tutoriels:
      - 01-tutoriels/index.md
  - Guides pratiques:
      - 02-guides-pratiques/index.md
  - Référence:
      - 03-reference/index.md
  - Explications:
      - 04-explications/index.md
"""

DEFAULT_VALE_INI = """StylesPath = .vale/styles
MinAlertLevel = suggestion

[*.md]
BasedOnStyles = STF100

# Enforce strict ASD-STF100 procedural checks on French How-To Guides and Runbooks
[docs/02-guides-pratiques/**/*.md]
BasedOnStyles = STF100
STF100.AbreviationsLatines = error
STF100.LocutionsLourdes = error
STF100.ModauxInterdits = error
STF100.PointVirgule = error
"""

DEFAULT_MARKDOWNLINT_JSON = """{
  "default": true,
  "MD013": {
    "line_length": 120,
    "code_blocks": false,
    "tables": false
  },
  "MD024": {
    "siblings_only": true
  },
  "MD033": false,
  "MD041": true,
  "MD046": {
    "style": "fenced"
  },
  "MD060": false
}
"""

DEFAULT_DOCS_CI_YML = """name: Documentation CI

on:
  push:
    branches:
      - main
    paths:
      - "docs/**"
      - "mkdocs.yml"
      - ".vale.ini"
      - ".vale/**"
      - ".markdownlint.json"
      - ".github/workflows/docs-ci.yml"
  pull_request:
    paths:
      - "docs/**"
      - "mkdocs.yml"
      - ".vale.ini"
      - ".vale/**"
      - ".markdownlint.json"
      - ".github/workflows/docs-ci.yml"

jobs:
  docs-quality:
    name: Validate Diataxis FR, STF, Lint, and MkDocs
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install MkDocs Material
        run: |
          python -m pip install --upgrade pip
          pip install mkdocs-material

      - name: Validate French Diataxis structure, links, governance, and STF
        run: |
          if command -v diataxis-fr-check >/dev/null 2>&1; then
            diataxis-fr-check docs --strict --check-stf
          elif [ -f "$HOME/.gemini/config/skills/diataxis-docs/scripts/diataxis_check_fr.py" ]; then
            python "$HOME/.gemini/config/skills/diataxis-docs/scripts/diataxis_check_fr.py" docs --strict --check-stf
          elif [ -f "scripts/diataxis_check_fr.py" ]; then
            python scripts/diataxis_check_fr.py docs --strict --check-stf
          else
            echo "diataxis_check_fr.py not found in workspace or runner; skipping."
          fi

      - name: Run markdownlint
        uses: DavidAnson/markdownlint-cli2-action@v19
        with:
          globs: |
            docs/**/*.md
          config: .markdownlint.json

      - name: Run Vale French STF100 checks
        uses: errata-ai/vale-action@v2
        with:
          files: docs/02-guides-pratiques
          fail_on_error: true

      - name: Build MkDocs site in strict mode
        run: mkdocs build --strict
"""

DEFAULT_VALE_MODAUX = """extends: existence
message: "Modal ou terme incertain interdit en ASD-STF100 : '%s'."
level: error
ignorecase: true
tokens:
  - devrait
  - devraient
  - pourrait
  - pourraient
  - serait
  - seraient
  - faudrait
  - éventuellement
  - potentiellement
  - susceptible de
"""

DEFAULT_VALE_LOCUTIONS = """extends: existence
message: "Locution lourde ou redondante détectée : '%s'. Utilisez un verbe direct à l'impératif."
level: warning
ignorecase: true
tokens:
  - afin de
  - en vue de
  - dans le but de
  - au niveau de
  - par le biais de
  - préalablement à
  - procéder à
  - effectuer un
  - effectuer une
  - à l'aide de
  - vous devez
  - il faut
  - il convient de
  - il est nécessaire de
"""

DEFAULT_VALE_POINT_VIRGULE = """extends: existence
message: "Point-virgule interdit en ASD-STF100 (Règle 8.1). Séparez en deux phrases."
level: error
nonword: true
scope: sentence
tokens:
  - ';'
"""

DEFAULT_VALE_ABREVIATIONS = """extends: existence
message: "Abréviation latine déconseillée : '%s' (GR-6). Écrivez l'expression complète en français."
level: warning
ignorecase: true
nonword: true
tokens:
  - '\\be\\.g\\.'
  - '\\bi\\.e\\.'
  - '\\betc\\.'
  - '\\bcf\\.'
"""

DEFAULT_CI_FILES: dict[str, str] = {
    "mkdocs.yml": DEFAULT_MKDOCS_YML,
    ".vale.ini": DEFAULT_VALE_INI,
    ".markdownlint.json": DEFAULT_MARKDOWNLINT_JSON,
    ".github/workflows/docs-ci.yml": DEFAULT_DOCS_CI_YML,
    ".vale/styles/STF100/ModauxInterdits.yml": DEFAULT_VALE_MODAUX,
    ".vale/styles/STF100/LocutionsLourdes.yml": DEFAULT_VALE_LOCUTIONS,
    ".vale/styles/STF100/PointVirgule.yml": DEFAULT_VALE_POINT_VIRGULE,
    ".vale/styles/STF100/AbreviationsLatines.yml": DEFAULT_VALE_ABREVIATIONS,
}

CI_TEMPLATE_MAPPING: list[tuple[str, str]] = [
    ("mkdocs.yml", "mkdocs.yml"),
    (".vale.ini", ".vale.ini"),
    (".markdownlint.json", ".markdownlint.json"),
    ("docs-ci.yml", ".github/workflows/docs-ci.yml"),
    ("vale-styles/STF100/ModauxInterdits.yml", ".vale/styles/STF100/ModauxInterdits.yml"),
    ("vale-styles/STF100/LocutionsLourdes.yml", ".vale/styles/STF100/LocutionsLourdes.yml"),
    ("vale-styles/STF100/PointVirgule.yml", ".vale/styles/STF100/PointVirgule.yml"),
    ("vale-styles/STF100/AbreviationsLatines.yml", ".vale/styles/STF100/AbreviationsLatines.yml"),
]


def resolve_templates_dir() -> Path | None:
    """Locate the French Docs-as-Code templates directory when bundled on disk."""
    script_path = Path(__file__).resolve()
    candidates = [
        script_path.parent.parent / "templates" / "fr" / "docs-as-code",
        script_path.parent.parent / "templates" / "docs-as-code",
    ]
    if len(script_path.parents) > 2:
        candidates.append(
            script_path.parents[2] / "skills" / "diataxis-docs-fr" / "templates" / "docs-as-code"
        )
    for candidate in candidates:
        # Ensure we do not accidentally pick up English templates when running inside diataxis-docs.
        if (candidate / "vale-styles" / "STF100" / "ModauxInterdits.yml").is_file():
            return candidate
    return None


def load_ci_templates(templates_dir: Path | None = None) -> dict[str, str]:
    """Load French Docs-as-Code configuration files from templates_dir or built-in defaults."""
    resolved_dir = resolve_templates_dir() if templates_dir is None else templates_dir
    if resolved_dir is None:
        return dict(DEFAULT_CI_FILES)

    if not resolved_dir.is_dir():
        raise FileNotFoundError(f"Missing Docs-as-Code templates directory: {resolved_dir}")

    contents: dict[str, str] = {}
    for src_rel, dest_rel in CI_TEMPLATE_MAPPING:
        src_path = resolved_dir / src_rel
        if not src_path.is_file():
            raise FileNotFoundError(f"Missing French Docs-as-Code template: {src_path}")
        contents[dest_rel] = src_path.read_text(encoding="utf-8")
    return contents


def build_scaffold_plan(
    profile: str,
    with_ci: bool,
    templates_dir: Path | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Build directory list and file mapping for the requested French Diataxis profile."""
    dirs = list(INFRA_DIRS if profile == "infra" else LOGICIEL_DIRS)
    files = dict(INDEX_FILES)

    if with_ci:
        dirs.extend([
            ".github",
            ".github/workflows",
            ".vale",
            ".vale/styles",
            ".vale/styles/STF100",
        ])
        files.update(load_ci_templates(templates_dir))

    return dirs, files


def scaffold(
    target_dir: Path,
    profile: str = "infra",
    with_ci: bool = False,
    dry_run: bool = False,
    force: bool = False,
    templates_dir: Path | None = None,
) -> list[str]:
    """Create the French Diataxis directory tree and starter index/CI files.

    Returns a list of human-readable operation log lines.
    """
    dirs, files = build_scaffold_plan(
        profile=profile,
        with_ci=with_ci,
        templates_dir=templates_dir,
    )
    actions: list[str] = []

    for rel_dir in dirs:
        dest_dir = target_dir / rel_dir
        if dest_dir.exists():
            actions.append(f"[EXISTS DIR] {dest_dir}")
            continue
        if dry_run:
            actions.append(f"[DRY-RUN CREATE DIR] {dest_dir}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            actions.append(f"[CREATE DIR] {dest_dir}")

    for rel_file, content in files.items():
        dest_file = target_dir / rel_file
        exists = dest_file.exists()

        if exists and not force:
            prefix = "[DRY-RUN SKIP]" if dry_run else "[SKIP]"
            actions.append(f"{prefix} {dest_file} (already exists; use --force to overwrite)")
            continue

        if dry_run:
            verb = "DRY-RUN OVERWRITE" if exists else "DRY-RUN WRITE"
            actions.append(f"[{verb}] {dest_file}")
        else:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(content, encoding="utf-8")
            verb = "OVERWRITE" if exists else "WRITE"
            actions.append(f"[{verb}] {dest_file}")

    return actions


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scaffold a French Diataxis documentation tree and Docs-as-Code configs."
    )
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Repository or project root directory where docs/ will be created.",
    )
    parser.add_argument(
        "--profile",
        choices=["infra", "logiciel"],
        default="infra",
        help="French documentation layout profile (default: infra).",
    )
    parser.add_argument(
        "--with-ci",
        action="store_true",
        help="Write mkdocs.yml, .vale.ini, .vale/styles/STF100/*.yml, .markdownlint.json, and docs-ci.yml.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned filesystem operations without modifying disk.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files instead of skipping them.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    if (
        getattr(sys.stdout, "encoding", None)
        and sys.stdout.encoding.lower() not in ("utf-8", "utf8")
        and hasattr(sys.stdout, "reconfigure")
    ):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv)
    try:
        actions = scaffold(
            target_dir=args.target_dir,
            profile=args.profile,
            with_ci=args.with_ci,
            dry_run=args.dry_run,
            force=args.force,
        )
    except (OSError, FileNotFoundError) as exc:
        print(f"[ERROR] Failed to scaffold French documentation: {exc}", file=sys.stderr)
        return 1

    for line in actions:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

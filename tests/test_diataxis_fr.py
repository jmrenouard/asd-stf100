#!/usr/bin/env python3
"""Pytest suite for French Diataxis tools, Docs-as-Code configs, skills, and docs/."""

from __future__ import annotations

import configparser
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SKILLS_DIR = REPO_ROOT / "skills"
STF_SKILL_DIR = SKILLS_DIR / "francais-technique-simplifie"
DIATAXIS_SKILL_DIR = SKILLS_DIR / "diataxis-docs-fr"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from asd_stf100 import diataxis_check_fr, scaffold_diataxis_fr  # noqa: E402


def _scaffold_clean_infra(tmp_path: Path) -> Path:
    """Create a clean infra French Diataxis docs tree and return docs_dir."""
    rc = scaffold_diataxis_fr.main([str(tmp_path), "--profile", "infra"])
    assert rc == 0
    return tmp_path / "docs"


# ---------------------------------------------------------------------------
# scaffold_diataxis_fr.py tests
# ---------------------------------------------------------------------------


def test_scaffold_infra_profile(tmp_path: Path) -> None:
    """Infra profile creates the full French subdirectory hierarchy and all index files."""
    rc = scaffold_diataxis_fr.main([str(tmp_path), "--profile", "infra"])
    assert rc == 0

    expected_dirs = [
        "docs/assets/architecture",
        "docs/assets/runbooks",
        "docs/01-tutoriels",
        "docs/02-guides-pratiques/deploiement",
        "docs/02-guides-pratiques/exploitation",
        "docs/02-guides-pratiques/gestion-incidents",
        "docs/02-guides-pratiques/securite",
        "docs/03-reference/architecture-specs",
        "docs/03-reference/configuration",
        "docs/03-reference/cli-et-scripts",
        "docs/03-reference/codes-erreurs",
        "docs/04-explications/vue-architecture",
        "docs/04-explications/decisions-architecture",
        "docs/04-explications/analyses-internes",
    ]
    for rel_dir in expected_dirs:
        assert (tmp_path / rel_dir).is_dir(), f"Missing directory: {rel_dir}"

    expected_indexes = [
        "docs/index.md",
        "docs/01-tutoriels/index.md",
        "docs/02-guides-pratiques/index.md",
        "docs/03-reference/index.md",
        "docs/04-explications/index.md",
    ]
    for rel_file in expected_indexes:
        assert (tmp_path / rel_file).is_file(), f"Missing index file: {rel_file}"


def test_scaffold_logiciel_profile(tmp_path: Path) -> None:
    """Logiciel profile creates docs/, assets/, and top-level quadrants without infra subdirs."""
    rc = scaffold_diataxis_fr.main([str(tmp_path), "--profile", "logiciel"])
    assert rc == 0

    for rel_dir in [
        "docs/assets/architecture",
        "docs/assets/runbooks",
        "docs/01-tutoriels",
        "docs/02-guides-pratiques",
        "docs/03-reference",
        "docs/04-explications",
    ]:
        assert (tmp_path / rel_dir).is_dir()

    assert not (tmp_path / "docs/02-guides-pratiques/gestion-incidents").exists()
    assert not (tmp_path / "docs/03-reference/codes-erreurs").exists()
    assert (tmp_path / "docs/index.md").is_file()


def test_scaffold_dry_run_makes_no_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--dry-run prints planned operations and writes nothing to disk."""
    target = tmp_path / "dry-run-repo"
    rc = scaffold_diataxis_fr.main(
        [str(target), "--profile", "infra", "--with-ci", "--dry-run"]
    )
    assert rc == 0
    assert not target.exists()

    captured = capsys.readouterr()
    assert "[DRY-RUN CREATE DIR]" in captured.out
    assert "[DRY-RUN WRITE]" in captured.out


def test_scaffold_with_ci_creates_toolchain_files(tmp_path: Path) -> None:
    """--with-ci writes mkdocs.yml, .vale.ini, .vale/styles/STF100/*.yml, .markdownlint.json, and docs-ci.yml."""
    rc = scaffold_diataxis_fr.main([str(tmp_path), "--profile", "infra", "--with-ci"])
    assert rc == 0

    expected_ci_files = [
        "mkdocs.yml",
        ".vale.ini",
        ".markdownlint.json",
        ".github/workflows/docs-ci.yml",
        ".vale/styles/STF100/ModauxInterdits.yml",
        ".vale/styles/STF100/LocutionsLourdes.yml",
        ".vale/styles/STF100/PointVirgule.yml",
        ".vale/styles/STF100/AbreviationsLatines.yml",
    ]
    for rel_file in expected_ci_files:
        assert (tmp_path / rel_file).is_file(), f"Missing CI file: {rel_file}"

    parsed_json = json.loads((tmp_path / ".markdownlint.json").read_text(encoding="utf-8"))
    assert parsed_json["default"] is True


def test_scaffold_no_overwrite_without_force_and_overwrite_with_force(
    tmp_path: Path,
) -> None:
    """Existing files are preserved by default and overwritten only when --force is passed."""
    assert scaffold_diataxis_fr.main([str(tmp_path), "--profile", "logiciel"]) == 0
    root_index = tmp_path / "docs/index.md"
    custom_text = "# Portail personnalisé\n\nConserver ce contenu.\n"
    root_index.write_text(custom_text, encoding="utf-8")

    assert scaffold_diataxis_fr.main([str(tmp_path), "--profile", "logiciel"]) == 0
    assert root_index.read_text(encoding="utf-8") == custom_text

    assert (
        scaffold_diataxis_fr.main([str(tmp_path), "--profile", "logiciel", "--force"])
        == 0
    )
    assert root_index.read_text(encoding="utf-8") != custom_text
    assert "Diátaxis" in root_index.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# diataxis_check_fr.py tests
# ---------------------------------------------------------------------------


def test_check_clean_scaffold_passes_strict(tmp_path: Path) -> None:
    """Fresh infra and logiciel scaffolds pass diataxis_check_fr.py --strict with exit 0."""
    infra_root = tmp_path / "infra"
    assert scaffold_diataxis_fr.main([str(infra_root), "--profile", "infra"]) == 0
    assert diataxis_check_fr.main([str(infra_root / "docs"), "--strict"]) == 0

    sw_root = tmp_path / "logiciel"
    assert scaffold_diataxis_fr.main([str(sw_root), "--profile", "logiciel"]) == 0
    assert diataxis_check_fr.main([str(sw_root / "docs"), "--strict"]) == 0


def test_check_missing_quadrant_fails(tmp_path: Path) -> None:
    """Missing a required French quadrant directory or index.md exits with code 1."""
    docs_dir = _scaffold_clean_infra(tmp_path)
    shutil.rmtree(docs_dir / "03-reference")
    assert diataxis_check_fr.main([str(docs_dir)]) == 1


def test_check_missing_quadrant_index_fails(tmp_path: Path) -> None:
    """Missing French quadrant index.md exits with code 1."""
    docs_dir = _scaffold_clean_infra(tmp_path)
    (docs_dir / "04-explications/index.md").unlink()
    assert diataxis_check_fr.main([str(docs_dir)]) == 1


def test_check_broken_relative_link_fails_and_code_links_ignored(
    tmp_path: Path,
) -> None:
    """Broken relative links fail with exit 1 while external, anchor, and code links are ignored."""
    docs_dir = _scaffold_clean_infra(tmp_path)
    safe_page = docs_dir / "01-tutoriels/lab-1.md"
    safe_page.write_text(
        "# Lab 1\n\n"
        "Externe valide : [Exemple](https://example.com/inexistant.md)\n"
        "Mailto valide : [Contact](mailto:ops@example.com)\n"
        "Ancre valide : [Section](#etape-1)\n"
        "Code en ligne : `[Casse](n-existe-pas.md)`\n\n"
        "```markdown\n[Bloc code](introuvable.md)\n```\n\n"
        "## Étape 1\n\nExécutez `echo ok`.\n",
        encoding="utf-8",
    )
    assert diataxis_check_fr.main([str(docs_dir), "--strict"]) == 0

    broken_page = docs_dir / "01-tutoriels/lab-2.md"
    broken_page.write_text(
        "# Lab 2\n\nVoir [Page manquante](../03-reference/fichier-absent.md#ancre).\n",
        encoding="utf-8",
    )
    assert diataxis_check_fr.main([str(docs_dir)]) == 1


def test_check_howto_governance_warnings_and_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """02-guides-pratiques/ triggers warnings on missing validation/rollback or theoretical headings."""
    docs_dir = _scaffold_clean_infra(tmp_path)
    bad_howto = docs_dir / "02-guides-pratiques/exploitation/mauvais-runbook.md"
    bad_howto.write_text(
        "# Redémarrer le service\n\n"
        "## Pourquoi cette panne arrive\n\nContexte général.\n\n"
        "## Architecture\n\nExplication du cluster.\n\n"
        "## Théorie\n\nDétail théorique.\n\n"
        "## Contexte\n\nHistorique.\n\n"
        "## Étapes\n\n1. Redémarrez le service.\n",
        encoding="utf-8",
    )

    assert diataxis_check_fr.main([str(docs_dir)]) == 0
    out = capsys.readouterr().out
    assert "Vérification/Validation" in out
    assert "Retour arrière/Restauration" in out
    assert "Theoretical heading" in out

    assert diataxis_check_fr.main([str(docs_dir), "--strict"]) == 1


def test_check_reference_governance_warnings_and_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """03-reference/ warns on missing table/list and tutorial phrasing."""
    docs_dir = _scaffold_clean_infra(tmp_path)
    bad_ref = docs_dir / "03-reference/configuration/mauvaise-ref.md"
    bad_ref.write_text(
        "# Paramètres serveur\n\n"
        "Dans ce tutoriel, commençons à l'Étape 1 de configuration.\n",
        encoding="utf-8",
    )

    assert diataxis_check_fr.main([str(docs_dir)]) == 0
    out = capsys.readouterr().out
    assert "lacks a structured Markdown table or structured list" in out
    assert "Tutorial phrasing" in out

    assert diataxis_check_fr.main([str(docs_dir), "--strict"]) == 1


def test_check_explanation_governance_warnings_and_strict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """04-explications/ warns on procedural headings such as Étape 1, Retour arrière, Remédiation, Prérequis."""
    docs_dir = _scaffold_clean_infra(tmp_path)
    bad_exp = docs_dir / "04-explications/decisions-architecture/mauvais-adr.md"
    bad_exp.write_text(
        "# ADR-002 : Topologie de file\n\n"
        "## Prérequis\n\nInstaller la CLI.\n\n"
        "## Étape 1 : Configurer le courtier\n\nExécuter la commande.\n\n"
        "## Remédiation\n\nRelancer.\n\n"
        "## Retour arrière\n\nRestaurer.\n",
        encoding="utf-8",
    )

    assert diataxis_check_fr.main([str(docs_dir)]) == 0
    out = capsys.readouterr().out
    assert out.count("Procedural heading") == 4

    assert diataxis_check_fr.main([str(docs_dir), "--strict"]) == 1


def test_check_stf_propagates_pass_fail_and_skill_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--check-stf propagates STF errors to exit code 1 and discovers sibling skill stf_check.py."""
    docs_dir = _scaffold_clean_infra(tmp_path / "unit")
    runbook = docs_dir / "02-guides-pratiques/exploitation/runbook.md"
    runbook.write_text(
        "# Runbook\n\n## Vérification\n\n1. Vérifiez la sortie.\n\n## Retour arrière\n\n1. Restaurez.\n",
        encoding="utf-8",
    )

    missing_stf = tmp_path / "missing-stf.py"
    monkeypatch.setattr(diataxis_check_fr, "DEFAULT_STF_SCRIPT", missing_stf)
    assert diataxis_check_fr.main([str(docs_dir), "--check-stf"]) == 1

    failing_stf = tmp_path / "fake_fail_stf.py"
    failing_stf.write_text("import sys\nprint('ERROR modal')\nsys.exit(1)\n", encoding="utf-8")
    monkeypatch.setattr(diataxis_check_fr, "DEFAULT_STF_SCRIPT", failing_stf)
    assert diataxis_check_fr.main([str(docs_dir), "--check-stf"]) == 1

    passing_stf = tmp_path / "fake_pass_stf.py"
    passing_stf.write_text("import sys\nprint('OK')\nsys.exit(0)\n", encoding="utf-8")
    monkeypatch.setattr(diataxis_check_fr, "DEFAULT_STF_SCRIPT", passing_stf)
    assert diataxis_check_fr.main([str(docs_dir), "--strict", "--check-stf"]) == 0


def test_skill_layout_discovers_sibling_stf_check(tmp_path: Path) -> None:
    """diataxis_check_fr.py inside a skills/<name>/scripts/ tree resolves ../../francais-technique-simplifie/scripts/stf_check.py."""
    fake_skills = tmp_path / "skills"
    stf_scripts = fake_skills / "francais-technique-simplifie" / "scripts"
    diataxis_scripts = fake_skills / "diataxis-docs" / "scripts"
    stf_scripts.mkdir(parents=True)
    diataxis_scripts.mkdir(parents=True)

    (stf_scripts / "stf_check.py").write_text(
        "import sys\nprint('STF_OK')\nsys.exit(0)\n", encoding="utf-8"
    )
    copied_checker = diataxis_scripts / "diataxis_check_fr.py"
    shutil.copyfile(SRC_DIR / "asd_stf100" / "diataxis_check_fr.py", copied_checker)

    docs_dir = _scaffold_clean_infra(tmp_path / "target")
    (docs_dir / "02-guides-pratiques/exploitation/test.md").write_text(
        "# Test\n\n## Vérification\n\n1. Testez.\n\n## Retour arrière\n\n1. Restaurez.\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(copied_checker), str(docs_dir), "--strict", "--check-stf"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "STF_OK" in proc.stdout


# ---------------------------------------------------------------------------
# Root Docs-as-Code configs and skills validation
# ---------------------------------------------------------------------------


def test_root_docs_as_code_configs_valid() -> None:
    """Root .markdownlint.json, .vale.ini, .vale/styles/STF100/*.yml, mkdocs.yml, and docs-ci.yml parse cleanly."""
    yaml = pytest.importorskip("yaml")

    mdlint = json.loads((REPO_ROOT / ".markdownlint.json").read_text(encoding="utf-8"))
    assert mdlint["default"] is True

    vale_raw = (REPO_ROOT / ".vale.ini").read_text(encoding="utf-8")
    parser = configparser.ConfigParser()
    parser.read_string("[DEFAULT]\n" + vale_raw)
    assert "docs/02-guides-pratiques/**/*.md" in parser.sections()
    assert parser["docs/02-guides-pratiques/**/*.md"]["MinAlertLevel"] == "error"
    assert "STF100" in parser["docs/02-guides-pratiques/**/*.md"]["BasedOnStyles"]

    vale_rules = [
        "ModauxInterdits.yml",
        "LocutionsLourdes.yml",
        "PointVirgule.yml",
        "AbreviationsLatines.yml",
    ]
    for rule_name in vale_rules:
        rule_path = REPO_ROOT / ".vale/styles/STF100" / rule_name
        assert rule_path.is_file(), f"Missing Vale rule: {rule_path}"
        parsed_rule = yaml.safe_load(rule_path.read_text(encoding="utf-8"))
        assert parsed_rule["extends"] == "existence"
        assert parsed_rule["tokens"]

    mkdocs_cfg = yaml.safe_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    assert mkdocs_cfg["theme"]["name"] == "material"
    assert mkdocs_cfg["theme"]["language"] == "fr"
    assert mkdocs_cfg["docs_dir"] == "docs"

    ci_cfg = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/docs-ci.yml").read_text(encoding="utf-8")
    )
    assert "jobs" in ci_cfg


def test_skills_frontmatter_and_script_parity() -> None:
    """Both French Agent Skills have valid YAML frontmatter and identical script copies."""
    yaml = pytest.importorskip("yaml")

    for skill_dir, expected_name in [
        (STF_SKILL_DIR, "francais-technique-simplifie"),
        (DIATAXIS_SKILL_DIR, "diataxis-docs-fr"),
    ]:
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.is_file()
        text = skill_md.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        _, fm_raw, _ = text.split("---", 2)
        fm = yaml.safe_load(fm_raw)
        assert fm["name"] == expected_name
        assert len(fm["description"].strip()) > 20

    assert (STF_SKILL_DIR / "LICENSE").is_file()
    assert (STF_SKILL_DIR / "NOTICE.md").is_file()
    assert (STF_SKILL_DIR / "examples/avant-apres.md").is_file()
    assert (STF_SKILL_DIR / "templates/procedure-runbook-fr.md").is_file()

    for script_name in ("scaffold_diataxis_fr.py", "diataxis_check_fr.py"):
        src_bytes = (SRC_DIR / "asd_stf100" / script_name).read_bytes()
        skill_bytes = (DIATAXIS_SKILL_DIR / "scripts" / script_name).read_bytes()
        assert src_bytes == skill_bytes, f"Script mismatch for {script_name}"

    # Verify embedded scaffold defaults match skill templates/docs-as-code files.
    templates_dir = DIATAXIS_SKILL_DIR / "templates" / "docs-as-code"
    disk_templates = scaffold_diataxis_fr.load_ci_templates(templates_dir)
    assert disk_templates == scaffold_diataxis_fr.DEFAULT_CI_FILES


def test_skill_runbook_templates_pass_governance_and_stf(tmp_path: Path) -> None:
    """French skill runbook templates pass diataxis_check_fr --strict and stf_check.py."""
    stf_script = SRC_DIR / "asd_stf100" / "stf_check.py"
    if not stf_script.is_file():
        pytest.skip("src/asd_stf100/stf_check.py not yet present in pre-merge branch.")

    for template_path in (
        STF_SKILL_DIR / "templates/procedure-runbook-fr.md",
        DIATAXIS_SKILL_DIR / "templates/02-guide-pratique-runbook.md",
    ):
        case_dir = tmp_path / template_path.stem
        docs_dir = _scaffold_clean_infra(case_dir)
        dest = docs_dir / "02-guides-pratiques/exploitation" / template_path.name
        shutil.copyfile(template_path, dest)

        (docs_dir / "03-reference/codes-erreurs/matrice-alertes.md").write_text(
            "# Matrice des alertes\n\n| Code | Runbook |\n| :--- | :--- |\n| HA-001 | Bascule |\n",
            encoding="utf-8",
        )
        (docs_dir / "04-explications/vue-architecture/index.md").write_text(
            "# Vue d'architecture\n\nIndex de l'architecture du système.\n",
            encoding="utf-8",
        )
        (docs_dir / "04-explications/vue-architecture/topologie.md").write_text(
            "# Topologie\n\nVue d'architecture du cluster.\n",
            encoding="utf-8",
        )

        findings, _, stf_out = diataxis_check_fr.validate_docs(
            docs_dir=docs_dir,
            strict=True,
            check_stf=True,
            stf_script=stf_script,
        )
        assert findings == [], f"{template_path} failed: {findings}\n{stf_out}"


def test_shallow_script_path_does_not_raise_index_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standalone copies in shallow directories (len(parents) <= 2) must not raise IndexError."""
    shallow_checker = Path("/scripts/diataxis_check_fr.py")
    monkeypatch.setattr(diataxis_check_fr, "__file__", str(shallow_checker))
    resolved_stf = diataxis_check_fr.find_default_stf_script()
    assert resolved_stf.name == "stf_check.py"

    shallow_scaffold = Path("/scripts/scaffold_diataxis_fr.py")
    monkeypatch.setattr(scaffold_diataxis_fr, "__file__", str(shallow_scaffold))
    assert scaffold_diataxis_fr.resolve_templates_dir() is None


def test_repo_docs_pass_diataxis_and_stf_strict() -> None:
    """Repository's own docs/ tree passes diataxis_check_fr --strict --check-stf with zero findings."""
    stf_script = SRC_DIR / "asd_stf100" / "stf_check.py"
    if not stf_script.is_file():
        pytest.skip("src/asd_stf100/stf_check.py not yet present in pre-merge branch.")

    findings, file_count, stf_out = diataxis_check_fr.validate_docs(
        docs_dir=REPO_ROOT / "docs",
        strict=True,
        check_stf=True,
        stf_script=stf_script,
    )
    assert file_count >= 18
    assert findings == [], f"Repo docs findings: {findings}\n{stf_out}"

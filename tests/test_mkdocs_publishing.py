"""Unit, integration, and workflow contract tests for versioned MkDocs Material publishing."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PUBLISH_PATH = REPO_ROOT / ".github" / "workflows" / "docs-publish.yml"
WORKFLOW_CI_PATH = REPO_ROOT / ".github" / "workflows" / "docs-ci.yml"
MKDOCS_CONFIG_PATH = REPO_ROOT / "mkdocs.yml"
HOOKS_SCRIPT_PATH = REPO_ROOT / "scripts" / "mkdocs_hooks.py"
BUILD_SCRIPT_PATH = REPO_ROOT / "scripts" / "build_versioned_docs.py"
REQUIREMENTS_DOCS_PATH = REPO_ROOT / "requirements-docs.txt"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"

BASE_PUBLIC_URL = "https://asd-stf100.lightpath.fr"
REPO_GITHUB_URL = "https://github.com/jmrenouard/asd-stf100"
SHA40_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class _MkDocsYamlLoader(yaml.SafeLoader):
    """Safe YAML loader supporting PyMdownx `!!python/name:` tag references as strings."""


def _python_name_multi_constructor(
    loader: yaml.Loader,
    tag_suffix: str,
    node: yaml.Node,
) -> str:
    """Represent PyMdownx `!!python/name:` tags as deterministic strings."""
    del loader, node
    return f"python/name:{tag_suffix}"


_MkDocsYamlLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:",
    _python_name_multi_constructor,
)


class _AttrDict(dict[str, Any]):
    """Dictionary exposing keys as attributes to mimic MkDocsConfig in hook tests."""

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def _load_mkdocs_config() -> dict[str, Any]:
    """Load and parse root `mkdocs.yml` using `_MkDocsYamlLoader`."""
    assert MKDOCS_CONFIG_PATH.is_file(), "mkdocs.yml must exist at repository root"
    loader = _MkDocsYamlLoader(MKDOCS_CONFIG_PATH.read_text(encoding="utf-8"))
    try:
        parsed = loader.get_single_data()
    finally:
        loader.dispose()
    assert isinstance(parsed, dict), "mkdocs.yml must parse into a YAML mapping"
    return parsed


def _load_script_module(module_name: str, script_path: Path) -> ModuleType:
    """Import a standalone script module by path without altering permanent sys.path."""
    assert script_path.is_file(), f"Missing script module: {script_path}"
    scripts_dir = str(script_path.parent)
    added_sys_path = False
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
        added_sys_path = True
    try:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        assert spec is not None and spec.loader is not None, f"Cannot load spec for {script_path}"
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if added_sys_path and scripts_dir in sys.path:
            sys.path.remove(scripts_dir)


def _flatten_nav_paths(node: Any) -> list[str]:
    """Collect all file paths from a nested MkDocs navigation structure."""
    paths: list[str] = []
    if isinstance(node, str):
        paths.append(node)
    elif isinstance(node, list):
        for item in node:
            paths.extend(_flatten_nav_paths(item))
    elif isinstance(node, dict):
        for val in node.values():
            paths.extend(_flatten_nav_paths(val))
    return paths


def _find_nav_section(nav: list[Any], section_name: str) -> Any:
    """Find a top-level section entry by title inside a MkDocs nav list."""
    for item in nav:
        if isinstance(item, dict) and section_name in item:
            return item[section_name]
    return None


def _collect_workflow_steps(job_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Return mapping entries from a workflow job's `steps` list."""
    steps = job_cfg.get("steps", [])
    assert isinstance(steps, list)
    return [step for step in steps if isinstance(step, dict)]


def _has_mkdocs_material() -> bool:
    """Return True when both `mkdocs` and `material` packages are importable."""
    return (
        importlib.util.find_spec("mkdocs") is not None
        and importlib.util.find_spec("material") is not None
    )


def _run_git(repo_dir: Path, *args: str) -> str:
    """Execute a git command in `repo_dir` and assert exit code 0."""
    proc = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"git {' '.join(args)} failed:\n{proc.stdout}\n{proc.stderr}"
    return proc.stdout


def _find_private_files(root_dir: Path) -> list[str]:
    """Return relative paths of any sensitive or log files found under `root_dir`."""
    return [
        p.relative_to(root_dir).as_posix()
        for p in root_dir.rglob("*")
        if p.is_file()
        and (
            p.suffix.lower() in {".kdbx", ".keyx", ".log"}
            or p.name.lower() == ".env"
            or p.name.lower().startswith(".env.")
        )
    ]


# ==============================================================================
# 1. mkdocs.yml and Portal Assets Verification
# ==============================================================================


def test_mkdocs_yml_configuration_and_portal_assets() -> None:
    """Verify mkdocs.yml Material config, Mermaid, mike switcher, hooks, exclusions, nav, and assets."""
    config = _load_mkdocs_config()

    assert config.get("site_name") == "ASD-STF100 — Français Technique Simplifié"
    assert config.get("site_url") == f"{BASE_PUBLIC_URL}/"
    assert config.get("repo_name") == "jmrenouard/asd-stf100"
    assert config.get("repo_url") == REPO_GITHUB_URL
    assert config.get("docs_dir") == "docs"
    assert "scripts/mkdocs_hooks.py" in config.get("hooks", [])

    theme = config.get("theme", {})
    assert isinstance(theme, dict)
    assert theme.get("name") == "material"
    assert theme.get("language") == "fr"
    assert theme.get("logo") == "assets/logo.svg"
    assert theme.get("favicon") == "assets/logo.svg"
    assert "navigation.tabs" in theme.get("features", [])
    assert "navigation.indexes" in theme.get("features", [])

    extra = config.get("extra", {})
    assert extra.get("version", {}).get("provider") == "mike"
    assert extra.get("version", {}).get("default") == "latest"

    extra_css = config.get("extra_css", [])
    assert "stylesheets/extra.css" in extra_css

    extensions = config.get("markdown_extensions", [])
    ext_names: set[str] = set()
    superfences_cfg: dict[str, Any] = {}
    for ext in extensions:
        if isinstance(ext, str):
            ext_names.add(ext)
        elif isinstance(ext, dict):
            ext_names.update(ext.keys())
            if "pymdownx.superfences" in ext:
                superfences_cfg = ext["pymdownx.superfences"] or {}

    assert "admonition" in ext_names
    assert "pymdownx.superfences" in ext_names

    custom_fences = superfences_cfg.get("custom_fences", [])
    mermaid_fences = [
        fence for fence in custom_fences if isinstance(fence, dict) and fence.get("name") == "mermaid"
    ]
    assert len(mermaid_fences) == 1, "pymdownx.superfences must configure a mermaid custom fence"
    assert mermaid_fences[0].get("class") == "mermaid"
    assert "fence_code_format" in str(mermaid_fences[0].get("format", ""))

    raw_exclude = config.get("exclude_docs", "")
    exclude_text = "\n".join(raw_exclude) if isinstance(raw_exclude, list) else str(raw_exclude)
    for pattern in ("*.kdbx", "*.keyx", "*.log", ".env"):
        assert pattern in exclude_text, f"exclude_docs must exclude '{pattern}'"

    nav = config.get("nav", [])
    assert isinstance(nav, list) and len(nav) == 6
    tab_names = [next(iter(entry.keys())) for entry in nav if isinstance(entry, dict)]
    assert tab_names == [
        "Accueil",
        "Tutoriels",
        "Guides pratiques",
        "Référence",
        "Explications",
        "Versions et gouvernance",
    ]

    guides_paths = _flatten_nav_paths(_find_nav_section(nav, "Guides pratiques"))
    assert "02-guides-pratiques/publier-documentation-ionos.md" in guides_paths

    explications_paths = _flatten_nav_paths(_find_nav_section(nav, "Explications"))
    assert "04-explications/adr-002-publication-mkdocs-versionnee.md" in explications_paths

    governance_paths = _flatten_nav_paths(_find_nav_section(nav, "Versions et gouvernance"))
    for virtual_doc in ("overview.md", "CHANGELOG.md", "CONTRIBUTING.md", "NOTICE.md"):
        assert virtual_doc in governance_paths

    assert (REPO_ROOT / "docs" / "index.md").is_file()
    assert (REPO_ROOT / "docs" / "stylesheets" / "extra.css").is_file()
    logo_svg = REPO_ROOT / "docs" / "assets" / "logo.svg"
    assert logo_svg.is_file()
    assert "<svg" in logo_svg.read_text(encoding="utf-8").lower()
    assert (REPO_ROOT / "docs" / "02-guides-pratiques" / "publier-documentation-ionos.md").is_file()
    assert (REPO_ROOT / "docs" / "04-explications" / "adr-002-publication-mkdocs-versionnee.md").is_file()


# ==============================================================================
# 2. scripts/mkdocs_hooks.py Unit Tests
# ==============================================================================


def test_mkdocs_hooks_convert_github_alerts_and_ignore_code_blocks() -> None:
    """Verify all 5 GitHub alerts convert to Material admonitions while fenced blocks stay untouched."""
    hooks = _load_script_module("mkdocs_hooks", HOOKS_SCRIPT_PATH)

    sample = (
        "Introduction.\n\n"
        "> [!NOTE]\n"
        "> Contexte utile.\n\n"
        "> [!TIP] Astuce\n"
        "> Optimisation pratique.\n\n"
        "> [!IMPORTANT]\n"
        "> Exigence essentielle.\n\n"
        "> [!WARNING]\n"
        "> Risque de dérive.\n\n"
        "> [!CAUTION]\n"
        "> Opération critique.\n\n"
        "```markdown\n"
        "> [!NOTE]\n"
        "> Exemple littéral dans un bloc de code.\n"
        "```\n\n"
        "~~~markdown\n"
        "> [!WARNING]\n"
        "> Autre bloc clôturé par tildes.\n"
        "~~~\n"
    )

    converted = hooks.convert_github_alerts(sample)

    assert "!!! note" in converted
    assert '!!! tip "Astuce"' in converted or "!!! tip" in converted
    assert "!!! info" in converted
    assert "!!! warning" in converted
    assert "!!! danger" in converted
    assert "Contexte utile." in converted
    assert "Opération critique." in converted

    outside_fenced, fenced_tail = converted.split("```markdown", 1)
    for marker in ("[!" + tag + "]" for tag in ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")):
        assert marker not in outside_fenced
    assert "> [!NOTE]" in fenced_tail
    assert "> [!WARNING]" in fenced_tail


def test_mkdocs_hooks_gfm_slugify() -> None:
    """Verify gfm_slugify produces GitHub-compatible TOC anchors including French accented headings."""
    hooks = _load_script_module("mkdocs_hooks", HOOKS_SCRIPT_PATH)

    assert hooks.gfm_slugify("Français Technique Simplifié") == "français-technique-simplifié"
    assert hooks.gfm_slugify("Matrice Diátaxis (FR)") == "matrice-diátaxis-fr"
    assert hooks.gfm_slugify("Règles de rédaction & Catégories") == "règles-de-rédaction--catégories"
    assert hooks.gfm_slugify("Procédure d'exploitation (étape 1)") == "procédure-dexploitation-étape-1"
    assert hooks.gfm_slugify("cli_flags") == "cli_flags"
    assert hooks.gfm_slugify("Alpha Beta", separator="_") == "alpha_beta"


def test_mkdocs_hooks_rewrite_relative_links_virtual_html_and_exclusions() -> None:
    """Verify virtual doc links, HTML asset depth, GitHub blob/tree URLs, and excluded target neutralization."""
    hooks = _load_script_module("mkdocs_hooks", HOOKS_SCRIPT_PATH)

    overview_md = (
        '<img src="docs/assets/logo.svg" alt="Logo" />\n'
        "- [Changelog](CHANGELOG.md)\n"
        "- [Contribuer](CONTRIBUTING.md)\n"
        "- [Notice](NOTICE.md)\n"
        "- [Portail](docs/index.md)\n"
        "- [Tutoriels](docs/01-tutoriels/index.md)\n"
        "- [Licence](LICENSE)\n"
        "- [PDF](dist/ASD-STF100_ISSUE1.pdf)\n"
        "- [Skills](skills/)\n"
        "- [Vault](secrets.kdbx)\n"
        "- [Key](vault.keyx)\n"
        "- [Log](build.log)\n"
        "- [Env](.env)\n"
        "- [EnvLocal](.env.local)\n"
        "```markdown\n"
        "[Preserved](CHANGELOG.md)\n"
        '<img src="docs/assets/logo.svg" />\n'
        "```\n"
    )

    rewritten_overview = hooks.rewrite_relative_links(
        overview_md,
        page_src_path="overview.md",
        ref="v1.0.0",
        use_directory_urls=True,
    )
    outside_fence, fenced_part = rewritten_overview.split("```markdown", 1)

    assert '<img src="../assets/logo.svg"' in outside_fence
    assert "](CHANGELOG.md)" in outside_fence
    assert "](CONTRIBUTING.md)" in outside_fence
    assert "](NOTICE.md)" in outside_fence
    assert "](index.md)" in outside_fence
    assert "](01-tutoriels/index.md)" in outside_fence
    assert f"]({REPO_GITHUB_URL}/blob/v1.0.0/LICENSE)" in outside_fence
    assert f"]({REPO_GITHUB_URL}/blob/v1.0.0/dist/ASD-STF100_ISSUE1.pdf)" in outside_fence
    assert f"]({REPO_GITHUB_URL}/tree/v1.0.0/skills/)" in outside_fence

    for forbidden_target in ("secrets.kdbx", "vault.keyx", "build.log", "(.env)", "(.env.local)"):
        assert forbidden_target not in outside_fence
    for kept_label in ("Vault", "Key", "Log", "Env", "EnvLocal"):
        assert kept_label in outside_fence

    assert "[Preserved](CHANGELOG.md)" in fenced_part
    assert '<img src="docs/assets/logo.svg" />' in fenced_part

    rewritten_flat = hooks.rewrite_relative_links(
        '<img src="docs/assets/logo.svg" alt="Logo" />\n',
        page_src_path="overview.md",
        ref="v1.0.0",
        use_directory_urls=False,
    )
    assert '<img src="assets/logo.svg"' in rewritten_flat

    contributing_md = (
        "- [Accueil](README.md)\n"
        "- [Référence](docs/03-reference/regles-redaction.md)\n"
        "- [Notice](NOTICE.md)\n"
        "- [Licence](LICENSE)\n"
    )
    rewritten_contrib = hooks.rewrite_relative_links(
        contributing_md,
        page_src_path="CONTRIBUTING.md",
        ref="v1.0.0",
        use_directory_urls=True,
    )
    assert "](overview.md)" in rewritten_contrib
    assert "](03-reference/regles-redaction.md)" in rewritten_contrib
    assert "](NOTICE.md)" in rewritten_contrib
    assert f"]({REPO_GITHUB_URL}/blob/v1.0.0/LICENSE)" in rewritten_contrib


def test_mkdocs_hooks_diataxis_depth_links_and_historical_fallbacks(tmp_path: Path) -> None:
    """Verify depth-1/depth-2 Diataxis rewriting and historical fallbacks when FR quadrants are absent."""
    hooks = _load_script_module("mkdocs_hooks", HOOKS_SCRIPT_PATH)

    depth1_md = (
        "- [README](../../README.md)\n"
        "- [Changelog](../../CHANGELOG.md)\n"
        "- [Contributing](../../CONTRIBUTING.md)\n"
        "- [Notice](../../NOTICE.md)\n"
        "- [Portail](../index.md)\n"
        "- [Ref](../03-reference/cli-et-codes-retour.md)\n"
        "- [Licence](../../LICENSE)\n"
        "- [PDF](../../dist/ASD-STF100_ISSUE1.pdf)\n"
        "- [Skills](../../skills/)\n"
    )
    rewritten_d1 = hooks.rewrite_relative_links(
        depth1_md,
        page_src_path="01-tutoriels/01-demarrage-rapide-stf100.md",
        ref="main",
    )
    assert "](../overview.md)" in rewritten_d1
    assert "](../CHANGELOG.md)" in rewritten_d1
    assert "](../CONTRIBUTING.md)" in rewritten_d1
    assert "](../NOTICE.md)" in rewritten_d1
    assert "](../index.md)" in rewritten_d1
    assert "](../03-reference/cli-et-codes-retour.md)" in rewritten_d1
    assert f"]({REPO_GITHUB_URL}/blob/main/LICENSE)" in rewritten_d1
    assert f"]({REPO_GITHUB_URL}/blob/main/dist/ASD-STF100_ISSUE1.pdf)" in rewritten_d1
    assert f"]({REPO_GITHUB_URL}/tree/main/skills/)" in rewritten_d1

    depth2_md = (
        "- [README](../../../README.md)\n"
        "- [Portail](../../index.md)\n"
        "- [Ref](../../03-reference/cli-et-codes-retour.md)\n"
        "- [Licence](../../../LICENSE)\n"
    )
    rewritten_d2 = hooks.rewrite_relative_links(
        depth2_md,
        page_src_path="02-guides-pratiques/exploitation/runbook.md",
        ref="main",
    )
    assert "](../../overview.md)" in rewritten_d2
    assert "](../../index.md)" in rewritten_d2
    assert "](../../03-reference/cli-et-codes-retour.md)" in rewritten_d2
    assert f"]({REPO_GITHUB_URL}/blob/main/LICENSE)" in rewritten_d2

    modern_docs = tmp_path / "modern_docs"
    for quadrant in ("01-tutoriels", "02-guides-pratiques", "03-reference", "04-explications"):
        (modern_docs / quadrant).mkdir(parents=True)
        (modern_docs / quadrant / "index.md").write_text(f"# {quadrant}\n", encoding="utf-8")
    (modern_docs / "01-tutoriels" / "01-demarrage-rapide-stf100.md").write_text("# Lab\n", encoding="utf-8")

    rewritten_modern = hooks.rewrite_relative_links(
        "- [T](01-tutoriels/index.md)\n- [TDir](01-tutoriels/)\n- [T1](01-tutoriels/01-demarrage-rapide-stf100.md)\n",
        page_src_path="index.md",
        ref="main",
        docs_dir=modern_docs,
    )
    assert "- [T](01-tutoriels/index.md)" in rewritten_modern
    assert "- [TDir](01-tutoriels/index.md)" in rewritten_modern
    assert "- [T1](01-tutoriels/01-demarrage-rapide-stf100.md)" in rewritten_modern

    historical_docs = tmp_path / "historical_docs"
    historical_docs.mkdir()
    portal_links = (
        "- [T](01-tutoriels/01-demarrage-rapide-stf100.md)\n"
        "- [H](02-guides-pratiques/index.md)\n"
    )
    rewritten_hist_virtual = hooks.rewrite_relative_links(
        portal_links,
        page_src_path="index.md",
        ref="v0.1.0",
        docs_dir=historical_docs,
        available_root_docs=["overview.md"],
    )
    assert "- [T](overview.md)" in rewritten_hist_virtual
    assert "- [H](overview.md)" in rewritten_hist_virtual

    rewritten_hist_github = hooks.rewrite_relative_links(
        portal_links,
        page_src_path="index.md",
        ref="v0.1.0",
        docs_dir=historical_docs,
        available_root_docs=[],
    )
    assert f"- [T]({REPO_GITHUB_URL}/blob/v0.1.0/README.md)" in rewritten_hist_github
    assert f"- [H]({REPO_GITHUB_URL}/blob/v0.1.0/README.md)" in rewritten_hist_github


def test_mkdocs_hooks_prune_nav_for_existing_files_and_discover_release_notes(tmp_path: Path) -> None:
    """Verify nav pruning removes missing entries/empty sections, keeps virtual docs, and sorts release notes."""
    hooks = _load_script_module("mkdocs_hooks", HOOKS_SCRIPT_PATH)

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Accueil\n", encoding="utf-8")
    (docs_dir / "RELEASE_NOTES_v1.0.0.md").write_text("# v1.0.0\n", encoding="utf-8")
    (docs_dir / "RELEASE_NOTES_v1.0.1.md").write_text("# v1.0.1\n", encoding="utf-8")
    (docs_dir / "RELEASE_NOTES_v1.10.0.md").write_text("# v1.10.0\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Présentation\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text("# Contribution\n", encoding="utf-8")
    # NOTICE.md intentionally omitted to verify missing virtual doc pruning

    nav = [
        {"Accueil": "index.md"},
        {
            "Guides pratiques": [
                {"Déploiement": ["02-guides-pratiques/deploiement/missing.md"]},
                "MISSING_DOC.md",
            ]
        },
        {
            "Versions et gouvernance": [
                {"Présentation générale": "overview.md"},
                {"Journal des modifications": "CHANGELOG.md"},
                {"Guide de contribution": "CONTRIBUTING.md"},
                {"Mentions légales et licences": "NOTICE.md"},
                {"Release Notes v9.9.9": "RELEASE_NOTES_v9.9.9.md"},
            ]
        },
    ]

    pruned = hooks.prune_nav_for_existing_files(nav, docs_dir, tmp_path)
    all_paths = _flatten_nav_paths(pruned)

    assert "index.md" in all_paths
    assert "overview.md" in all_paths
    assert "CHANGELOG.md" in all_paths
    assert "CONTRIBUTING.md" in all_paths
    assert "NOTICE.md" not in all_paths
    assert "MISSING_DOC.md" not in all_paths
    assert "02-guides-pratiques/deploiement/missing.md" not in all_paths
    assert "RELEASE_NOTES_v9.9.9.md" not in all_paths
    assert _find_nav_section(pruned, "Guides pratiques") is None

    releases_section = _find_nav_section(pruned, "Versions et gouvernance")
    assert releases_section is not None
    release_paths = _flatten_nav_paths(releases_section)
    for note in ("RELEASE_NOTES_v1.10.0.md", "RELEASE_NOTES_v1.0.1.md", "RELEASE_NOTES_v1.0.0.md"):
        assert note in release_paths

    assert release_paths.index("RELEASE_NOTES_v1.10.0.md") < release_paths.index("RELEASE_NOTES_v1.0.1.md")
    assert release_paths.index("RELEASE_NOTES_v1.0.1.md") < release_paths.index("RELEASE_NOTES_v1.0.0.md")


def test_mkdocs_hooks_on_config_edit_uri_and_virtual_edit_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify on_config sets edit_uri on main/WORKTREE, clears on tags, attaches gfm_slugify, and updates edit_url."""
    hooks = _load_script_module("mkdocs_hooks", HOOKS_SCRIPT_PATH)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Accueil\n", encoding="utf-8")

    monkeypatch.setenv("ASD_STF100_DOCS_REF", "WORKTREE")
    monkeypatch.setenv("ASD_STF100_DOCS_SITE_URL", f"{BASE_PUBLIC_URL}/main")
    cfg_main = _AttrDict(
        {
            "docs_dir": str(docs_dir),
            "site_url": "",
            "edit_uri": "",
            "repo_url": REPO_GITHUB_URL,
            "mdx_configs": {"toc": {"permalink": True}},
            "nav": [{"Accueil": "index.md"}],
        }
    )
    hooks.on_config(cfg_main)
    assert cfg_main["edit_uri"] == "edit/main/docs/"
    assert cfg_main["site_url"] == f"{BASE_PUBLIC_URL}/main/"
    assert cfg_main["mdx_configs"]["toc"]["slugify"] is hooks.gfm_slugify

    class _FakeFile:
        def __init__(self, src_uri: str) -> None:
            self.src_uri = src_uri
            self.src_path = src_uri

    class _FakeFiles:
        def get_file_from_path(self, path: str) -> None:
            del path

    class _FakePage:
        def __init__(self, src_uri: str, edit_url: str | None) -> None:
            self.file = _FakeFile(src_uri)
            self.edit_url = edit_url

    for virtual_uri, repo_file in (
        ("overview.md", "README.md"),
        ("CHANGELOG.md", "CHANGELOG.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        ("NOTICE.md", "NOTICE.md"),
    ):
        page_main = _FakePage(
            virtual_uri,
            f"{REPO_GITHUB_URL}/edit/main/docs/{virtual_uri}",
        )
        hooks.on_page_markdown("# Section\n", page_main, cfg_main, _FakeFiles())
        assert page_main.edit_url == f"{REPO_GITHUB_URL}/edit/main/{repo_file}"

    monkeypatch.setenv("ASD_STF100_DOCS_REF", "v1.0.0")
    cfg_tag = _AttrDict(
        {
            "docs_dir": str(docs_dir),
            "site_url": "",
            "edit_uri": "edit/main/docs/",
            "repo_url": REPO_GITHUB_URL,
            "mdx_configs": {"toc": {}},
            "nav": [],
        }
    )
    hooks.on_config(cfg_tag)
    assert cfg_tag["edit_uri"] == ""

    page_tag = _FakePage(
        "overview.md",
        f"{REPO_GITHUB_URL}/edit/main/docs/overview.md",
    )
    hooks.on_page_markdown("# Section\n", page_tag, cfg_tag, _FakeFiles())
    assert not page_tag.edit_url


def test_mkdocs_hooks_on_files_excludes_secrets_and_injects_virtual_docs(tmp_path: Path) -> None:
    """Verify on_files excludes secret/log files and injects root virtual Markdown documents."""
    if importlib.util.find_spec("mkdocs") is None:
        pytest.skip("mkdocs is not installed in current test environment")

    from mkdocs.structure.files import File, Files

    hooks = _load_script_module("mkdocs_hooks", HOOKS_SCRIPT_PATH)
    docs_dir = tmp_path / "docs"
    site_dir = tmp_path / "site"
    docs_dir.mkdir()
    site_dir.mkdir()
    (docs_dir / "index.md").write_text("# Accueil\n", encoding="utf-8")
    (docs_dir / "vault.kdbx").write_text("secret", encoding="utf-8")
    (docs_dir / ".env").write_text("TOKEN=x", encoding="utf-8")
    (docs_dir / "run.log").write_text("log", encoding="utf-8")
    for root_file in ("README.md", "CHANGELOG.md", "CONTRIBUTING.md", "NOTICE.md"):
        (tmp_path / root_file).write_text(f"# {root_file}\n", encoding="utf-8")

    cfg = _AttrDict(
        {
            "docs_dir": str(docs_dir),
            "site_dir": str(site_dir),
            "use_directory_urls": True,
        }
    )
    initial_files = Files(
        [
            File("index.md", str(docs_dir), str(site_dir), True),
            File("vault.kdbx", str(docs_dir), str(site_dir), True),
            File(".env", str(docs_dir), str(site_dir), True),
            File("run.log", str(docs_dir), str(site_dir), True),
        ]
    )
    resulting_files = hooks.on_files(initial_files, cfg)
    uris = {f.src_uri for f in resulting_files}

    assert "index.md" in uris
    assert "vault.kdbx" not in uris
    assert ".env" not in uris
    assert "run.log" not in uris
    for virtual_uri in ("overview.md", "CHANGELOG.md", "CONTRIBUTING.md", "NOTICE.md"):
        assert virtual_uri in uris


def test_mkdocs_hooks_importable_without_mkdocs_or_pathspec(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify scripts/mkdocs_hooks.py imports and runs without mkdocs or pathspec installed."""
    for blocked in (
        "mkdocs",
        "mkdocs.structure",
        "mkdocs.structure.files",
        "pathspec",
        "pathspec.gitignore",
    ):
        monkeypatch.setitem(sys.modules, blocked, None)

    try:
        hooks = _load_script_module("mkdocs_hooks_no_deps", HOOKS_SCRIPT_PATH)
        assert "!!! note" in hooks.convert_github_alerts("> [!NOTE]\n> Fonctionne sans mkdocs.")
        assert hooks.gfm_slugify("Français Simplifié") == "français-simplifié"
        assert "](../overview.md)" in hooks.rewrite_relative_links(
            "[Accueil](../../README.md)",
            "01-tutoriels/01-demarrage-rapide-stf100.md",
        )
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.md").write_text("# Accueil\n", encoding="utf-8")
        cfg = _AttrDict(
            {
                "docs_dir": str(docs_dir),
                "site_url": "",
                "edit_uri": "",
                "mdx_configs": {"toc": {}},
                "nav": [{"Accueil": "index.md"}],
            }
        )
        hooks.on_config(cfg)
        assert cfg["edit_uri"] == "edit/main/docs/"
    finally:
        sys.modules.pop("mkdocs_hooks_no_deps", None)


# ==============================================================================
# 3. scripts/build_versioned_docs.py Unit & Integration Tests
# ==============================================================================


def test_build_versioned_docs_parse_semver_tag_and_manifest_ordering() -> None:
    """Verify semver parsing, descending ordering, alias assignment, and empty-tag fallback."""
    builder = _load_script_module("build_versioned_docs", BUILD_SCRIPT_PATH)

    assert builder.parse_semver_tag("v1.0.0") == (1, 0, 0)
    assert builder.parse_semver_tag("v1.0.1") == (1, 0, 1)
    assert builder.parse_semver_tag("v1.10.0") == (1, 10, 0)
    assert builder.parse_semver_tag("main") is None
    assert builder.parse_semver_tag("latest") is None
    assert builder.parse_semver_tag("v1.0") is None

    manifest = builder.build_versions_manifest(
        ["v1.0.0", "v1.2.0", "v1.10.0", "v1.0.1"],
        include_main=True,
    )
    versions = [entry["version"] for entry in manifest]
    assert versions.index("v1.10.0") < versions.index("v1.2.0")
    assert versions.index("v1.2.0") < versions.index("v1.0.1")
    assert versions.index("v1.0.1") < versions.index("v1.0.0")

    by_version = {entry["version"]: entry for entry in manifest}
    assert "latest" in by_version["v1.10.0"]["aliases"]
    assert "latest" not in by_version["v1.0.1"]["aliases"]
    assert "main" in by_version
    assert by_version["main"]["title"] == "main (dev)"
    assert "dev" in by_version["main"]["aliases"]

    fallback_main = builder.build_versions_manifest([], include_main=True)
    assert len(fallback_main) == 1
    assert fallback_main[0]["version"] == "main"
    assert fallback_main[0]["title"] == "main (dev)"
    assert set(fallback_main[0]["aliases"]) == {"latest", "dev"}

    assert builder.build_versions_manifest([], include_main=False) == []


def test_build_versioned_site_rejects_protected_or_ancestor_output_dirs(tmp_path: Path) -> None:
    """Verify build_versioned_site refuses to overwrite repo root, ancestors, or protected directories."""
    builder = _load_script_module("build_versioned_docs", BUILD_SCRIPT_PATH)
    repo_dir = tmp_path / "repo"
    protected_names = (".git", ".github", "src", "docs", "tests", "scripts", "spec", "skills", "dist")
    for name in protected_names:
        (repo_dir / name).mkdir(parents=True)
    sentinel = repo_dir / "docs" / "keep.md"
    sentinel.write_text("# Keep\n", encoding="utf-8")

    forbidden_targets = [
        repo_dir,
        tmp_path,
        repo_dir / "docs" / "nested",
        *(repo_dir / name for name in protected_names),
    ]
    for forbidden_out in forbidden_targets:
        with pytest.raises(ValueError):
            builder.build_versioned_site(repo_root=repo_dir, output_dir=forbidden_out, skip_tags=True)
        assert sentinel.is_file()


def test_build_versioned_docs_render_htaccess_and_redirect_html() -> None:
    """Verify .htaccess rules (HTTPS 301, /latest/ & /dev/ 302, security headers, no Indexes) and redirect HTML."""
    builder = _load_script_module("build_versioned_docs", BUILD_SCRIPT_PATH)

    htaccess = builder.render_htaccess("v1.0.0", main_version="main")
    assert "Options -Indexes" in htaccess
    assert "DirectoryIndex index.html" in htaccess
    assert "RewriteEngine On" in htaccess
    assert "RewriteBase /" in htaccess
    assert "X-Content-Type-Options" in htaccess
    assert "R=301" in htaccess
    assert "^latest(?:/(.*))?$" in htaccess
    assert "/v1.0.0/$1" in htaccess
    assert "^dev(?:/(.*))?$" in htaccess
    assert "/main/$1" in htaccess
    assert "R=302" in htaccess
    assert "ErrorDocument 404 /v1.0.0/404.html" in htaccess

    redirect_html = builder.render_redirect_html("/v1.0.0/", "ASD-STF100 — Documentation")
    assert "<!doctype html>" in redirect_html.lower()
    assert 'lang="fr"' in redirect_html.lower()
    assert "ASD-STF100 — Documentation" in redirect_html
    assert 'http-equiv="refresh"' in redirect_html.lower()
    assert "/v1.0.0/" in redirect_html


def test_assert_no_private_files_rejects_sensitive_artifacts(tmp_path: Path) -> None:
    """Verify assert_no_private_files accepts clean trees and raises on vault/env/log leaks."""
    builder = _load_script_module("build_versioned_docs", BUILD_SCRIPT_PATH)
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    (clean_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    builder.assert_no_private_files(clean_dir)

    for offender in ("vault.kdbx", "vault.keyx", "run.log", ".env", ".env.prod"):
        dirty_dir = tmp_path / f"dirty_{offender.replace('.', '_')}"
        dirty_dir.mkdir()
        (dirty_dir / offender).write_text("secret", encoding="utf-8")
        with pytest.raises(RuntimeError):
            builder.assert_no_private_files(dirty_dir)


def test_build_versioned_docs_end_to_end_worktree(tmp_path: Path) -> None:
    """End-to-end build of current repo WORKTREE handling zero-tag fallback and asset/privacy guarantees."""
    if not _has_mkdocs_material():
        pytest.skip("mkdocs and mkdocs-material are not installed in current test environment")
    if not (REPO_ROOT / ".git").exists() or shutil.which("git") is None:
        pytest.skip("Git repository metadata required for WORKTREE build test")

    builder = _load_script_module("build_versioned_docs", BUILD_SCRIPT_PATH)
    discovered_tags = builder.discover_release_tags(REPO_ROOT)

    out_dir = tmp_path / "site_dist"
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT_PATH),
            "--output",
            str(out_dir),
            "--base-url",
            BASE_PUBLIC_URL,
            "--main-ref",
            "WORKTREE",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"build_versioned_docs.py failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    expected_files = [
        out_dir / "versions.json",
        out_dir / "index.html",
        out_dir / ".htaccess",
        out_dir / "latest" / "index.html",
        out_dir / "dev" / "index.html",
        out_dir / "main" / "index.html",
        out_dir / "main" / "stylesheets" / "extra.css",
        out_dir / "main" / "assets" / "logo.svg",
        out_dir / "main" / "overview" / "index.html",
        out_dir / "main" / "CHANGELOG" / "index.html",
        out_dir / "main" / "CONTRIBUTING" / "index.html",
        out_dir / "main" / "NOTICE" / "index.html",
    ]
    for path in expected_files:
        assert path.is_file(), f"Expected built artifact missing: {path}"

    manifest = json.loads((out_dir / "versions.json").read_text(encoding="utf-8"))
    assert isinstance(manifest, list) and len(manifest) >= 1
    by_version = {entry["version"]: entry for entry in manifest}
    assert "main" in by_version

    htaccess_text = (out_dir / ".htaccess").read_text(encoding="utf-8")
    assert "/main/$1" in htaccess_text

    if not discovered_tags:
        assert len(manifest) == 1
        assert set(by_version["main"]["aliases"]) == {"latest", "dev"}
        assert "RewriteRule ^latest(?:/(.*))?$ /main/$1" in htaccess_text
    else:
        newest_tag = discovered_tags[0]
        assert "latest" in by_version[newest_tag]["aliases"]
        assert "dev" in by_version["main"]["aliases"]
        assert (out_dir / newest_tag / "index.html").is_file()
        assert f"/{newest_tag}/$1" in htaccess_text

    leaked_sensitive = _find_private_files(out_dir)
    assert not leaked_sensitive, f"Sensitive or log files leaked into built output: {leaked_sensitive}"


def test_build_versioned_docs_end_to_end_synthetic_multiversion_git_repo(tmp_path: Path) -> None:
    """End-to-end build in a temporary Git repo with v1.0.0, v1.1.0, and main verifying manifest and aliases."""
    if not _has_mkdocs_material():
        pytest.skip("mkdocs and mkdocs-material are not installed in current test environment")
    if shutil.which("git") is None:
        pytest.skip("git executable required for synthetic multi-version repository test")

    synth_repo = tmp_path / "synth_repo"
    synth_repo.mkdir()
    shutil.copy2(MKDOCS_CONFIG_PATH, synth_repo / "mkdocs.yml")
    (synth_repo / "scripts").mkdir()
    shutil.copy2(HOOKS_SCRIPT_PATH, synth_repo / "scripts" / "mkdocs_hooks.py")
    shutil.copytree(REPO_ROOT / "docs", synth_repo / "docs")
    for root_file in ("README.md", "CHANGELOG.md", "CONTRIBUTING.md", "NOTICE.md", "LICENSE"):
        shutil.copy2(REPO_ROOT / root_file, synth_repo / root_file)

    _run_git(synth_repo, "init")
    _run_git(synth_repo, "checkout", "-B", "main")
    _run_git(synth_repo, "config", "user.name", "Test Runner")
    _run_git(synth_repo, "config", "user.email", "test@example.com")
    _run_git(synth_repo, "config", "commit.gpgsign", "false")
    _run_git(synth_repo, "config", "tag.gpgsign", "false")

    _run_git(synth_repo, "add", "-A")
    _run_git(synth_repo, "commit", "-m", "chore: initial v1.0.0 documentation snapshot")
    _run_git(synth_repo, "tag", "v1.0.0")

    changelog_path = synth_repo / "CHANGELOG.md"
    changelog_path.write_text(
        changelog_path.read_text(encoding="utf-8") + "\n## [1.1.0] — Synthetic\n\n- Release v1.1.0.\n",
        encoding="utf-8",
    )
    _run_git(synth_repo, "add", "CHANGELOG.md")
    _run_git(synth_repo, "commit", "-m", "docs: prepare v1.1.0 release")
    _run_git(synth_repo, "tag", "v1.1.0")

    changelog_path.write_text(
        changelog_path.read_text(encoding="utf-8") + "\n- Unreleased main update.\n",
        encoding="utf-8",
    )
    _run_git(synth_repo, "add", "CHANGELOG.md")
    _run_git(synth_repo, "commit", "-m", "docs: advance main after v1.1.0")

    out_dir = tmp_path / "synth_site_dist"
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT_PATH),
            "--repo-root",
            str(synth_repo),
            "--output",
            str(out_dir),
            "--base-url",
            BASE_PUBLIC_URL,
            "--main-ref",
            "WORKTREE",
        ],
        cwd=str(synth_repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Synthetic multi-version build failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    for rel_file in (
        "versions.json",
        "index.html",
        ".htaccess",
        "v1.0.0/index.html",
        "v1.1.0/index.html",
        "main/index.html",
        "main/stylesheets/extra.css",
        "main/assets/logo.svg",
        "latest/index.html",
        "dev/index.html",
    ):
        assert (out_dir / rel_file).is_file(), f"Missing multi-version artifact: {rel_file}"

    manifest = json.loads((out_dir / "versions.json").read_text(encoding="utf-8"))
    versions_order = [entry["version"] for entry in manifest]
    assert versions_order.index("v1.1.0") < versions_order.index("v1.0.0")

    by_version = {entry["version"]: entry for entry in manifest}
    assert "latest" in by_version["v1.1.0"]["aliases"]
    assert "latest" not in by_version["v1.0.0"]["aliases"]
    assert by_version["main"]["title"] == "main (dev)"
    assert "dev" in by_version["main"]["aliases"]

    htaccess_text = (out_dir / ".htaccess").read_text(encoding="utf-8")
    assert "/v1.1.0/$1" in htaccess_text
    assert "/main/$1" in htaccess_text
    assert "../v1.1.0/" in (out_dir / "latest" / "index.html").read_text(encoding="utf-8")
    assert "../main/" in (out_dir / "dev" / "index.html").read_text(encoding="utf-8")
    assert "./v1.1.0/" in (out_dir / "index.html").read_text(encoding="utf-8")
    assert not _find_private_files(out_dir)


# ==============================================================================
# 4. GitHub Workflows, Requirements, and .gitignore Contract Tests
# ==============================================================================


def test_docs_publish_workflow_triggers_permissions_build_and_sftp_deploy() -> None:
    """Verify docs-publish.yml triggers, SHA pinning, least-privilege permissions, artifact flags, and SFTP steps."""
    assert WORKFLOW_PUBLISH_PATH.is_file(), ".github/workflows/docs-publish.yml must exist"
    raw_yaml = WORKFLOW_PUBLISH_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_yaml)
    assert isinstance(data, dict)

    assert data.get("permissions") == {"contents": "read"}

    triggers = data.get("on") if "on" in data else data.get(True)
    assert isinstance(triggers, dict)
    assert triggers["push"]["branches"] == ["main"]
    assert triggers["pull_request"]["branches"] == ["main"]
    assert triggers["push"]["paths"] == triggers["pull_request"]["paths"]
    for required_path in (
        "docs/**",
        "mkdocs.yml",
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "NOTICE.md",
        "requirements-docs.txt",
        ".vale.ini",
        ".markdownlint.json",
        "scripts/mkdocs_hooks.py",
        "scripts/build_versioned_docs.py",
        ".github/workflows/docs-ci.yml",
        ".github/workflows/docs-publish.yml",
        "tests/test_diataxis_fr.py",
        "tests/test_mkdocs_publishing.py",
    ):
        assert required_path in triggers["push"]["paths"]

    assert triggers["release"] == {"types": ["published"]}
    deploy_input = triggers["workflow_dispatch"]["inputs"]["deploy"]
    assert deploy_input["type"] == "boolean"
    assert deploy_input["default"] is True

    concurrency = data.get("concurrency", {})
    assert "docs-publish-" in str(concurrency.get("group", ""))
    assert "github.ref" in str(concurrency.get("group", ""))
    assert "pull_request" in str(concurrency.get("cancel-in-progress", ""))

    jobs = data.get("jobs", {})
    assert "verify-and-build" in jobs
    assert "deploy-ionos" in jobs

    for job_name, job_cfg in jobs.items():
        if isinstance(job_cfg.get("if"), str):
            assert "secrets." not in job_cfg["if"], f"{job_name}.if must not reference secrets."
        for idx, step in enumerate(_collect_workflow_steps(job_cfg)):
            uses_val = step.get("uses")
            if isinstance(uses_val, str):
                assert "@" in uses_val, f"{job_name} step #{idx} must pin action to SHA: {uses_val}"
                sha = uses_val.split("@", 1)[1]
                assert SHA40_RE.fullmatch(sha), (
                    f"{job_name} step #{idx} must use 40-char SHA, got '{uses_val}'"
                )
            if_val = step.get("if")
            if isinstance(if_val, str):
                assert "secrets." not in if_val, f"{job_name} step #{idx} must not use secrets. in if:"
            run_val = step.get("run")
            if isinstance(run_val, str):
                assert "${{" not in run_val, (
                    f"{job_name} step #{idx} must pass GitHub expressions via env:, never ${{{{ in run:"
                )

    build_job = jobs["verify-and-build"]
    assert build_job.get("runs-on") == "ubuntu-latest"
    assert isinstance(build_job.get("timeout-minutes"), int) and build_job["timeout-minutes"] <= 15

    build_steps = _collect_workflow_steps(build_job)
    checkout_steps = [s for s in build_steps if str(s.get("uses", "")).startswith("actions/checkout@")]
    assert len(checkout_steps) == 1
    assert checkout_steps[0].get("with", {}).get("fetch-depth") == 0

    python_steps = [s for s in build_steps if str(s.get("uses", "")).startswith("actions/setup-python@")]
    assert len(python_steps) == 1
    python_with = python_steps[0].get("with", {})
    assert python_with.get("python-version") == "3.12"
    assert python_with.get("cache") == "pip"
    assert python_with.get("cache-dependency-path") == "requirements-docs.txt"

    build_run_script = "\n".join(str(s.get("run", "")) for s in build_steps)
    for expected_cmd in (
        "requirements-docs.txt",
        "scripts/sync_docs.py --check",
        "asd_stf100.diataxis_check_fr docs --strict --check-stf",
        "tests/test_diataxis_fr.py",
        "tests/test_mkdocs_publishing.py",
        "scripts/build_versioned_docs.py",
        BASE_PUBLIC_URL,
        "origin/main",
        "WORKTREE",
        "site_dist/versions.json",
        "site_dist/.htaccess",
    ):
        assert expected_cmd in build_run_script

    upload_steps = [s for s in build_steps if str(s.get("uses", "")).startswith("actions/upload-artifact@")]
    assert len(upload_steps) == 1
    upload_with = upload_steps[0].get("with", {})
    assert upload_with.get("name") == "mkdocs-site-dist"
    assert upload_with.get("path") == "site_dist/"
    assert upload_with.get("include-hidden-files") is True
    if "retention-days" in upload_with:
        assert isinstance(upload_with["retention-days"], int) and upload_with["retention-days"] > 0

    deploy_job = jobs["deploy-ionos"]
    assert deploy_job.get("needs") == "verify-and-build"
    assert deploy_job.get("runs-on") == "ubuntu-latest"
    assert isinstance(deploy_job.get("timeout-minutes"), int) and deploy_job["timeout-minutes"] <= 15

    deploy_if = str(deploy_job.get("if", ""))
    assert "github.event_name == 'release'" in deploy_if
    assert "refs/heads/main" in deploy_if
    assert "inputs.deploy == true" in deploy_if

    deploy_steps = _collect_workflow_steps(deploy_job)
    assert not any("actions/checkout" in str(s.get("uses", "")) for s in deploy_steps)

    download_steps = [s for s in deploy_steps if str(s.get("uses", "")).startswith("actions/download-artifact@")]
    assert len(download_steps) == 1
    assert download_steps[0].get("with", {}).get("name") == "mkdocs-site-dist"
    assert download_steps[0].get("with", {}).get("path") == "."

    sftp_steps = [s for s in deploy_steps if str(s.get("uses", "")).startswith("wlixcc/SFTP-Deploy-Action@")]
    assert len(sftp_steps) == 2, "Expected full site upload step plus explicit .htaccess upload step"

    local_paths = [step.get("with", {}).get("local_path") for step in sftp_steps]
    assert "./" in local_paths
    assert ".htaccess" in local_paths

    for step in sftp_steps:
        step_with = step.get("with", {})
        assert step_with.get("sftp_only") is True
        assert step_with.get("server") == "${{ secrets.IONOS_FTP_SERVER }}"
        assert step_with.get("username") == "${{ secrets.IONOS_FTP_USERNAME }}"
        assert step_with.get("password") == "${{ secrets.IONOS_FTP_PASSWORD }}"
        assert "secrets.IONOS_FTP_PORT" in str(step_with.get("port", ""))
        assert "secrets.IONOS_REMOTE_PATH" in str(step_with.get("remote_path", ""))

    deploy_run_script = "\n".join(str(s.get("run", "")) for s in deploy_steps)
    assert ".htaccess" in deploy_run_script
    assert "versions.json" in deploy_run_script
    assert f"{BASE_PUBLIC_URL}/versions.json" in deploy_run_script
    assert f"{BASE_PUBLIC_URL}/latest/" in deploy_run_script
    assert f"{BASE_PUBLIC_URL}/main/" in deploy_run_script

    for unsafe_pattern in (
        "chmod 777",
        "chmod -R 777",
        "chmod a+rwx",
        "sudo",
        "eval ",
        "curl -s | bash",
        "wget -O- | sh",
    ):
        assert unsafe_pattern not in raw_yaml, f"Unsafe shell pattern found in workflow: {unsafe_pattern}"


def test_docs_ci_workflow_uses_requirements_docs_and_hooks_paths() -> None:
    """Verify docs-ci.yml pins MkDocs dependencies via requirements-docs.txt and watches hooks/reqs."""
    assert WORKFLOW_CI_PATH.is_file(), ".github/workflows/docs-ci.yml must exist"
    data = yaml.safe_load(WORKFLOW_CI_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)

    triggers = data.get("on") if "on" in data else data.get(True)
    assert isinstance(triggers, dict)
    for event_name in ("push", "pull_request"):
        paths = triggers[event_name]["paths"]
        assert "requirements-docs.txt" in paths
        assert "scripts/mkdocs_hooks.py" in paths

    jobs = data.get("jobs", {})
    assert "docs-quality" in jobs
    steps = _collect_workflow_steps(jobs["docs-quality"])
    run_script = "\n".join(str(step.get("run", "")) for step in steps)
    assert "requirements-docs.txt" in run_script


def test_gitignore_pyproject_and_requirements_docs_configuration() -> None:
    """Verify .gitignore excludes site_dist/, requirements-docs.txt pins MkDocs <2.0, and pyproject defines docs."""
    gitignore_lines = {
        line.strip()
        for line in GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    for entry in ("site/", "site_dist/", ".pytest_cache/", "__pycache__/"):
        assert entry in gitignore_lines, f".gitignore must exclude '{entry}'"

    assert REQUIREMENTS_DOCS_PATH.is_file(), "requirements-docs.txt must exist"
    reqs = REQUIREMENTS_DOCS_PATH.read_text(encoding="utf-8")
    req_lines = {
        line.strip()
        for line in reqs.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert any(line.startswith("mkdocs") and "<2.0" in line for line in req_lines)
    assert any(line.startswith("mkdocs-material") and "<10.0" in line for line in req_lines)
    assert any(line.startswith("pymdown-extensions") for line in req_lines)

    pyproject_text = PYPROJECT_PATH.read_text(encoding="utf-8")
    assert "docs =" in pyproject_text or "docs=" in pyproject_text
    assert "pyyaml" in pyproject_text.lower()

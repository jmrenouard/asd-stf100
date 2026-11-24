"""Executable verification tests for tutorials, how-to CLIs, diagrams, and language rules."""

from __future__ import annotations

import importlib.util
import io
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
SPEC_DIR = REPO_ROOT / "spec"
DOCS_DIR = REPO_ROOT / "docs"
TUTORIALS_DIR = DOCS_DIR / "01-tutoriels"
HOWTO_DIR = DOCS_DIR / "02-guides-pratiques"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from asd_stf100.stf_check import Report, check_text, load_dictionary  # noqa: E402

SKIP_DIRS = {".git", ".venv", ".pytest_cache", "node_modules", "site", "site_dist"}
FENCE_OPEN_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")
MERMAID_HEADER_RE = re.compile(
    r"^(?:flowchart(?:-elk)?(?:\s+(?:TD|TB|LR|RL|BT))?|graph\s+(?:TD|TB|LR|RL|BT)|"
    r"sequenceDiagram|stateDiagram(?:-v2)?|classDiagram|erDiagram|gantt|pie|"
    r"gitGraph|mindmap|timeline|xychart-beta)\b"
)
BOX_CORNER_RE = re.compile(r"[┌┐┘╔╗╚╝]")
ASCII_BOX_EDGE_RE = re.compile(r"\+[-=]{2,}\+")
FLOW_ARROW_RE = re.compile(r"(?<![<!])-->|(?<!<!)<--|(?<![=])==>|─+>")
TABLE_RULE_RE = re.compile(r"^[+┌├└╠╞╚][─━═\-=+:┬┼┴╦╬╩]+[+┐┤┘╗╣╝]$")
MULTI_COL_RULE_RE = re.compile(r"(?:[┬┼┴╦╬╩]|^\+[^+]*\+[^+]*\+)")
TREE_BRANCH_RE = re.compile(r"[├└]─")
FRENCH_STOPWORD_RE = re.compile(
    r"\b(?:les|des|une|pour|avec|dans|sur|qui|est|sont|vérifier|procédure|fichier)\b",
    re.IGNORECASE,
)


def _extract_fenced_blocks(markdown: str) -> list[dict[str, Any]]:
    """Parse CommonMark fenced code blocks with indentation and language metadata."""
    blocks: list[dict[str, Any]] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    open_line = 0
    open_indent = ""
    open_lang = ""
    body_lines: list[str] = []

    for lineno, line in enumerate(markdown.splitlines(), start=1):
        if not in_fence:
            match = FENCE_OPEN_RE.match(line)
            if not match:
                continue
            indent, fence, info = match.groups()
            if fence[0] == "`" and "`" in info:
                continue
            in_fence = True
            fence_char = fence[0]
            fence_len = len(fence)
            open_line = lineno
            open_indent = indent
            stripped = info.strip()
            open_lang = stripped.split()[0].lower().lstrip(".") if stripped else ""
            body_lines = []
        else:
            if re.match(rf"^[ \t]*{re.escape(fence_char)}{{{fence_len},}}[ \t]*$", line):
                blocks.append(
                    {
                        "line": open_line,
                        "indent": open_indent,
                        "lang": open_lang,
                        "body": "\n".join(body_lines),
                    }
                )
                in_fence = False
            else:
                body_lines.append(line)
    return blocks


def _run_module(module_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run an installed or workspace package module CLI and return the completed process."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}{os.pathsep}{existing_pp}" if existing_pp else str(SRC_DIR)
    return subprocess.run(
        [sys.executable, "-m", module_name, *args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _is_directory_tree_or_cli_table(body: str, lang: str) -> bool:
    """Distinguish directory trees and pipe-delimited CLI/SQL tables from ASCII diagrams."""
    cleaned = re.sub(r"<!--[\s\S]*?-->|\[[=\->\s]+\]", " ", body)
    has_arrows = bool(FLOW_ARROW_RE.search(cleaned))
    if TREE_BRANCH_RE.search(body) and not (BOX_CORNER_RE.search(body) or ASCII_BOX_EDGE_RE.search(body) or has_arrows):
        return True
    if has_arrows:
        return False

    non_empty = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not non_empty:
        return False
    has_border = any(TABLE_RULE_RE.match(ln) for ln in non_empty) or bool(ASCII_BOX_EDGE_RE.search(body))
    if not has_border:
        return False
    pipe_lines = sum(1 for ln in non_empty if ln.startswith(("|", "│")))
    if (pipe_lines / len(non_empty)) > 0.45:
        return True
    all_grid = all(
        TABLE_RULE_RE.match(ln) or (ln.startswith("|") and ln.endswith("|")) or (ln.startswith("│") and ln.endswith("│"))
        for ln in non_empty
    )
    return all_grid and (any(MULTI_COL_RULE_RE.search(ln) for ln in non_empty) or lang in {"sql", "mysql", "psql"})


def test_tutorial_01_demarrage_rapide_verbatim_execution(tmp_path: Path) -> None:
    """Execute Tutorial 1 non-compliant and compliant Markdown snippets via stf_check."""
    tutorial = (TUTORIALS_DIR / "01-demarrage-rapide-stf100.md").read_text(encoding="utf-8")
    blocks = _extract_fenced_blocks(tutorial)
    md_blocks = [b["body"] for b in blocks if b["lang"] == "markdown"]
    assert len(md_blocks) == 2, "Tutorial 1 must include failing and passing Markdown blocks"

    proc_file = tmp_path / "procedure_test.md"

    # Step 2: intentionally non-compliant procedure must match documented 5 errors, 3 warnings.
    proc_file.write_text(md_blocks[0] + "\n", encoding="utf-8")
    res_bad = _run_module("asd_stf100.stf_check", "--mode", "procedural", str(proc_file))
    assert res_bad.returncode == 1
    assert "Result: 5 errors, 3 warnings." in res_bad.stdout
    for expected_rule in ("[rule 5.1/6.3]", "[rule 8.1]", "[rule 3.2]", "[rule 3.6]", "[rule 1.1]"):
        assert expected_rule in res_bad.stdout
    assert "Result: 5 errors, 3 warnings." in tutorial

    # Step 3: fixed procedure must exit 0 with zero errors and zero warnings.
    proc_file.write_text(md_blocks[1] + "\n", encoding="utf-8")
    res_good = _run_module("asd_stf100.stf_check", "--mode", "procedural", str(proc_file))
    assert res_good.returncode == 0, res_good.stdout + res_good.stderr
    assert "Result: 0 errors, 0 warnings." in res_good.stdout
    assert "Result: 0 errors, 0 warnings." in tutorial


def test_tutorial_02_diataxis_fr_scaffold_and_check_end_to_end(tmp_path: Path) -> None:
    """Execute Tutorial 2 dry-run, infra --with-ci scaffold, verifier-service runbook, and strict check."""
    tutorial = (TUTORIALS_DIR / "02-initialiser-doc-diataxis-fr.md").read_text(encoding="utf-8")
    blocks = _extract_fenced_blocks(tutorial)
    md_blocks = [b["body"] for b in blocks if b["lang"] == "markdown"]
    assert len(md_blocks) == 1, "Tutorial 2 must embed the verifier-service.md runbook block"

    demo_dir = tmp_path / "demo-diataxis-fr"
    res_dry = _run_module(
        "asd_stf100.scaffold_diataxis_fr",
        str(demo_dir),
        "--profile",
        "infra",
        "--with-ci",
        "--dry-run",
    )
    assert res_dry.returncode == 0, res_dry.stderr
    assert "[DRY-RUN CREATE DIR]" in res_dry.stdout
    assert "[DRY-RUN WRITE]" in res_dry.stdout
    assert not demo_dir.exists()

    res_real = _run_module(
        "asd_stf100.scaffold_diataxis_fr",
        str(demo_dir),
        "--profile",
        "infra",
        "--with-ci",
    )
    assert res_real.returncode == 0, res_real.stderr

    runbook = demo_dir / "docs" / "02-guides-pratiques" / "exploitation" / "verifier-service.md"
    runbook.write_text(md_blocks[0] + "\n", encoding="utf-8")

    res_chk = _run_module(
        "asd_stf100.diataxis_check_fr",
        str(demo_dir / "docs"),
        "--strict",
        "--check-stf",
    )
    assert res_chk.returncode == 0, res_chk.stdout + res_chk.stderr
    assert "Summary: 0 error(s), 0 warning(s) across 6 markdown file(s)." in res_chk.stdout
    assert "Summary: 0 error(s), 0 warning(s) across 6 markdown file(s)." in tutorial

    scaffold_mkdocs = (demo_dir / "mkdocs.yml").read_text(encoding="utf-8")
    assert "name: mermaid" in scaffold_mkdocs

    if importlib.util.find_spec("mkdocs") and importlib.util.find_spec("material"):
        mermaid_page = demo_dir / "docs" / "04-explications" / "topologie.md"
        mermaid_page.write_text(
            "# Topologie\n\n```mermaid\nflowchart LR\n    Client[\"Client\"] --> Service[\"Service\"]\n```\n",
            encoding="utf-8",
        )
        site_out = tmp_path / "demo-site"
        res_mk = subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "--strict", "-d", str(site_out)],
            cwd=str(demo_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert res_mk.returncode == 0, res_mk.stdout + res_mk.stderr
        rendered = (site_out / "04-explications" / "topologie" / "index.html").read_text(encoding="utf-8")
        assert 'class="mermaid"' in rendered


def test_howto_guides_cli_and_dictionary_inflections() -> None:
    """Verify documented CLI entrypoints, script --help flags, How-To STF compliance, and fixed inflections."""
    cli_ref = (DOCS_DIR / "03-reference" / "cli-et-codes-retour.md").read_text(encoding="utf-8")
    for flag in ("--mode", "--dict", "--no-vocab", "--profile", "--with-ci", "--dry-run", "--force", "--strict", "--check-stf"):
        assert flag in cli_ref

    for mod in ("asd_stf100.stf_check", "asd_stf100.scaffold_diataxis_fr", "asd_stf100.diataxis_check_fr"):
        res = _run_module(mod, "--help")
        assert res.returncode == 0, f"{mod} --help failed: {res.stderr}"

    scripts_to_check = ["sync_docs.py", "build_versioned_docs.py"]
    if importlib.util.find_spec("reportlab") is not None:
        scripts_to_check.append("build_pdf.py")
    for script_name in scripts_to_check:
        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / script_name), "--help"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert res.returncode == 0, f"{script_name} --help failed: {res.stderr}"

    # Verify ACTUEL and OPÉRATIONNEL feminine inflections load cleanly with zero unknown warnings.
    vocab = load_dictionary(SPEC_DIR / "dictionary.json")
    rep = Report()
    check_text(
        "La version actuelle et la procédure opérationnelle restent valides.",
        "descriptive",
        rep,
        "inflections.md",
        vocab,
    )
    assert not rep.errors and not rep.warnings
    assert "actuelle" not in rep.unknown
    assert "opérationnelle" not in rep.unknown

    # Verify all non-index operational How-To guides pass strict STF procedural mode.
    howto_files = sorted(p for p in HOWTO_DIR.rglob("*.md") if p.name != "index.md")
    assert len(howto_files) >= 6
    res_stf = _run_module("asd_stf100.stf_check", "--mode", "procedural", *[str(p) for p in howto_files])
    assert res_stf.returncode == 0, res_stf.stdout + res_stf.stderr
    assert "Result: 0 errors, 0 warnings." in res_stf.stdout


def test_repo_markdown_diagram_hygiene_and_python_english_comments() -> None:
    """Enforce zero ASCII/indented/untagged diagrams across .md files and English comments in .py files."""
    md_files: list[Path] = []
    for root_str, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for fname in sorted(files):
            if fname.lower().endswith(".md"):
                md_files.append(Path(root_str) / fname)

    assert len(md_files) >= 35
    violations: list[str] = []
    for md_path in md_files:
        rel = md_path.relative_to(REPO_ROOT).as_posix()
        text = md_path.read_text(encoding="utf-8")
        for blk in _extract_fenced_blocks(text):
            if blk["lang"] == "mermaid":
                if blk["indent"]:
                    violations.append(f"{rel}:{blk['line']} indented mermaid fence")
                continue
            first_non_empty = next(
                (ln.strip() for ln in blk["body"].splitlines() if ln.strip() and not ln.strip().startswith("%%")),
                "",
            )
            if blk["lang"] not in {"diff", "patch"} and MERMAID_HEADER_RE.match(first_non_empty):
                if not (blk["lang"] in {"markdown", "md"} and "```mermaid" in blk["body"]):
                    violations.append(f"{rel}:{blk['line']} untagged mermaid block ({blk['lang'] or 'none'})")
                    continue
            if blk["lang"] not in {"diff", "patch", "sql", "mysql", "psql"} and not _is_directory_tree_or_cli_table(blk["body"], blk["lang"]):
                if BOX_CORNER_RE.search(blk["body"]) or ASCII_BOX_EDGE_RE.search(blk["body"]) or FLOW_ARROW_RE.search(blk["body"]):
                    violations.append(f"{rel}:{blk['line']} ASCII box or flow diagram in {blk['lang'] or 'none'} fence")

    assert violations == [], "Markdown diagram hygiene violations:\n" + "\n".join(violations)

    # Verify Python comments across src/, scripts/, and tests/ stay strictly English
    # (ignoring quoted/parenthesized French linguistic example tokens).
    french_comments: list[str] = []
    for folder in (SRC_DIR, SCRIPTS_DIR, REPO_ROOT / "tests"):
        for py_file in sorted(folder.rglob("*.py")):
            src = py_file.read_text(encoding="utf-8")
            for tok in tokenize.generate_tokens(io.StringIO(src).readline):
                if tok.type == tokenize.COMMENT:
                    cleaned = re.sub(r'\([^)]*\)|"[^"]*"', " ", tok.string)
                    if FRENCH_STOPWORD_RE.search(cleaned):
                        french_comments.append(f"{py_file.relative_to(REPO_ROOT)}:{tok.start[0]} {tok.string}")
    assert french_comments == [], "French comments detected in Python files:\n" + "\n".join(french_comments)

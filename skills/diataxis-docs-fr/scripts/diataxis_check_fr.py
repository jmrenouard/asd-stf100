#!/usr/bin/env python3
"""Validate French Diataxis structure, internal Markdown links, governance, and ASD-STF100."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

REQUIRED_QUADRANTS = (
    "01-tutoriels",
    "02-guides-pratiques",
    "03-reference",
    "04-explications",
)


def find_default_stf_script() -> Path:
    """Locate stf_check.py as a package sibling, sibling skill script, or repo source."""
    script_path = Path(__file__).resolve()
    candidates = [script_path.parent / "stf_check.py"]
    if len(script_path.parents) > 2:
        candidates.extend([
            script_path.parents[2] / "francais-technique-simplifie" / "scripts" / "stf_check.py",
            script_path.parents[2] / "src" / "asd_stf100" / "stf_check.py",
        ])
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


_INITIAL_DEFAULT_STF_SCRIPT = find_default_stf_script()
DEFAULT_STF_SCRIPT = _INITIAL_DEFAULT_STF_SCRIPT

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S+")

EXTERNAL_SCHEME_RE = re.compile(r"^(?:https?|mailto|ftp|tel|data):", re.IGNORECASE)

HOWTO_VALIDATION_RE = re.compile(
    r"\b(?:vérification|validation|vérifier|valider|contrôle)\b",
    re.IGNORECASE,
)
HOWTO_ROLLBACK_RE = re.compile(
    r"\b(?:retour\s+arrière|restauration|restaurer|annulation|rétablissement)\b",
    re.IGNORECASE,
)
HOWTO_THEORY_HEADING_RE = re.compile(
    r"\b(?:pourquoi|architecture|théorie|contexte|explication)\b",
    re.IGNORECASE,
)

REF_TUTORIAL_PHRASING_RE = re.compile(
    r"(?:\bdans\s+ce\s+tutoriel\b|\bétape\s+1\b|\bcommençons\b)",
    re.IGNORECASE,
)

EXPLANATION_PROCEDURAL_HEADING_RE = re.compile(
    r"\b(?:étape\s+\d+|retour\s+arrière|remédiation|prérequis)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    """Represents one validation error or governance warning."""

    severity: str
    path: Path
    line: int
    message: str

    def format(self) -> str:
        """Render the finding in a consistent CLI line format."""
        loc = f"{self.path}:{self.line}" if self.line > 0 else str(self.path)
        return f"[{self.severity}] {loc}: {self.message}"


def strip_inline_code(line: str) -> str:
    """Replace CommonMark inline code spans with spaces in linear time."""
    if "`" not in line:
        return line

    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] != "`":
            out.append(line[i])
            i += 1
            continue

        tick_len = 0
        while i + tick_len < n and line[i + tick_len] == "`":
            tick_len += 1

        search_pos = i + tick_len
        close_pos = -1
        while search_pos < n:
            if line[search_pos] != "`":
                search_pos += 1
                continue
            run_len = 0
            while search_pos + run_len < n and line[search_pos + run_len] == "`":
                run_len += 1
            if run_len == tick_len:
                close_pos = search_pos + run_len
                break
            search_pos += run_len

        if close_pos != -1:
            out.append(" ")
            i = close_pos
        else:
            out.append(line[i : i + tick_len])
            i += tick_len

    return "".join(out)


def extract_non_code_lines(text: str) -> list[tuple[int, str]]:
    """Return 1-based (line_number, line_without_inline_code) outside fenced code blocks."""
    result: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if fence_char is not None:
            if re.match(rf"^\s*{re.escape(fence_char)}{{{fence_len},}}\s*$", raw_line):
                fence_char = None
                fence_len = 0
            continue

        fence_match = FENCE_RE.match(raw_line)
        if fence_match:
            marker = fence_match.group(1)
            fence_char = marker[0]
            fence_len = len(marker)
            continue

        result.append((lineno, strip_inline_code(raw_line)))

    return result


def check_required_structure(docs_dir: Path) -> list[Finding]:
    """Verify docs/index.md and all four French quadrant directories with their index.md files."""
    findings: list[Finding] = []
    root_index = docs_dir / "index.md"
    if not root_index.is_file():
        findings.append(
            Finding("ERROR", root_index, 0, "Missing required documentation portal index.md.")
        )

    for quadrant in REQUIRED_QUADRANTS:
        quadrant_dir = docs_dir / quadrant
        if not quadrant_dir.is_dir():
            findings.append(
                Finding(
                    "ERROR",
                    quadrant_dir,
                    0,
                    f"Missing required French quadrant directory '{quadrant}'.",
                )
            )
            continue
        quadrant_index = quadrant_dir / "index.md"
        if not quadrant_index.is_file():
            findings.append(
                Finding("ERROR", quadrant_index, 0, f"Missing required '{quadrant}/index.md'.")
            )

    return findings


def normalize_link_target(raw_target: str) -> str:
    """Extract the file path portion of a Markdown link destination."""
    target = raw_target.strip()
    if not target:
        return ""
    if target.startswith("<"):
        end_idx = target.find(">")
        if end_idx != -1:
            target = target[1:end_idx].strip()
    else:
        target = target.split()[0]

    if not target or target.startswith("#"):
        return ""
    if EXTERNAL_SCHEME_RE.match(target) or target.startswith("//"):
        return ""

    target = target.split("#", 1)[0].split("?", 1)[0]
    return unquote(target.strip())


def check_relative_links(
    md_file: Path,
    docs_dir: Path,
    non_code_lines: list[tuple[int, str]],
) -> list[Finding]:
    """Verify that every relative Markdown link resolves to an existing target."""
    findings: list[Finding] = []
    for lineno, line in non_code_lines:
        for match in LINK_RE.finditer(line):
            target = normalize_link_target(match.group(1))
            if not target:
                continue

            if target.startswith("/"):
                resolved = (docs_dir / target.lstrip("/")).resolve()
            else:
                resolved = (md_file.parent / target).resolve()

            target_exists = resolved.is_file() or (
                resolved.is_dir() and (resolved / "index.md").is_file()
            )
            if not target_exists:
                findings.append(
                    Finding(
                        "ERROR",
                        md_file,
                        lineno,
                        f"Broken relative link target '{match.group(1).strip()}' (resolved to {resolved}).",
                    )
                )
    return findings


def check_quadrant_governance(
    md_file: Path,
    docs_dir: Path,
    non_code_lines: list[tuple[int, str]],
) -> list[Finding]:
    """Run French quadrant-specific genre-mixing heuristics on non-index Markdown files."""
    if md_file.name.lower() == "index.md":
        return []

    rel_parts = md_file.relative_to(docs_dir).parts
    if len(rel_parts) < 2:
        return []

    quadrant = rel_parts[0]
    findings: list[Finding] = []
    headings: list[tuple[int, str]] = []
    for lineno, line in non_code_lines:
        h_match = HEADING_RE.match(line)
        if h_match:
            headings.append((lineno, h_match.group(1)))

    full_text = "\n".join(line for _, line in non_code_lines)

    if quadrant == "02-guides-pratiques":
        if not HOWTO_VALIDATION_RE.search(full_text):
            findings.append(
                Finding(
                    "WARN",
                    md_file,
                    0,
                    "How-To / Runbook is missing a validation section or keyword (Vérification/Validation).",
                )
            )

        if not HOWTO_ROLLBACK_RE.search(full_text):
            findings.append(
                Finding(
                    "WARN",
                    md_file,
                    0,
                    "How-To / Runbook is missing a rollback section or keyword (Retour arrière/Restauration).",
                )
            )

        for lineno, heading in headings:
            if HOWTO_THEORY_HEADING_RE.search(heading):
                findings.append(
                    Finding(
                        "WARN",
                        md_file,
                        lineno,
                        f"Theoretical heading '## {heading}' belongs in 04-explications/, not 02-guides-pratiques/.",
                    )
                )

    elif quadrant == "03-reference":
        has_table = any(TABLE_ROW_RE.match(line) for _, line in non_code_lines)
        has_list = any(LIST_ITEM_RE.match(line) for _, line in non_code_lines)
        if not (has_table or has_list):
            findings.append(
                Finding(
                    "WARN",
                    md_file,
                    0,
                    "Reference document lacks a structured Markdown table or structured list.",
                )
            )

        for lineno, line in non_code_lines:
            match = REF_TUTORIAL_PHRASING_RE.search(line)
            if match:
                findings.append(
                    Finding(
                        "WARN",
                        md_file,
                        lineno,
                        f"Tutorial phrasing '{match.group(0)}' does not belong in 03-reference/.",
                    )
                )

    elif quadrant == "04-explications":
        for lineno, heading in headings:
            if EXPLANATION_PROCEDURAL_HEADING_RE.search(heading):
                findings.append(
                    Finding(
                        "WARN",
                        md_file,
                        lineno,
                        f"Procedural heading '## {heading}' belongs in 02-guides-pratiques/, not 04-explications/.",
                    )
                )

    return findings


def _resolve_stf_script(stf_script: Path | None) -> Path:
    """Resolve the STF linter path, preserving explicit overrides and monkeypatches."""
    if stf_script is not None:
        return stf_script
    if DEFAULT_STF_SCRIPT.is_file():
        return DEFAULT_STF_SCRIPT
    if DEFAULT_STF_SCRIPT != _INITIAL_DEFAULT_STF_SCRIPT:
        # Preserve monkeypatched missing path during unit tests.
        return DEFAULT_STF_SCRIPT
    return find_default_stf_script()


def run_stf_checks(
    docs_dir: Path,
    stf_script: Path | None = None,
) -> tuple[list[Finding], str]:
    """Run stf_check.py in procedural mode on non-index files under 02-guides-pratiques/."""
    target_script = _resolve_stf_script(stf_script)
    if not target_script.is_file():
        return (
            [
                Finding(
                    "ERROR",
                    target_script,
                    0,
                    f"STF linter script not found at expected path: {target_script}",
                )
            ],
            "",
        )

    howto_dir = docs_dir / "02-guides-pratiques"
    if not howto_dir.is_dir():
        return [], ""

    howto_files = sorted(
        path for path in howto_dir.rglob("*.md") if path.name.lower() != "index.md"
    )
    if not howto_files:
        return [], ""

    cmd = [
        sys.executable,
        str(target_script),
        "--mode",
        "procedural",
        *[str(path) for path in howto_files],
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    combined_output = "\n".join(
        part.strip() for part in (proc.stdout, proc.stderr) if part.strip()
    )

    findings: list[Finding] = []
    if proc.returncode != 0:
        findings.append(
            Finding(
                "ERROR",
                howto_dir,
                0,
                f"ASD-STF100 procedural validation failed with exit code {proc.returncode}.",
            )
        )
    return findings, combined_output


def validate_docs(
    docs_dir: Path,
    strict: bool = False,
    check_stf: bool = False,
    stf_script: Path | None = None,
) -> tuple[list[Finding], int, str]:
    """Validate French Diataxis docs directory and return (findings, file_count, stf_output)."""
    findings: list[Finding] = []
    findings.extend(check_required_structure(docs_dir))

    md_files = sorted(docs_dir.rglob("*.md"))
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        non_code_lines = extract_non_code_lines(text)
        findings.extend(check_relative_links(md_file, docs_dir, non_code_lines))
        findings.extend(check_quadrant_governance(md_file, docs_dir, non_code_lines))

    stf_output = ""
    if check_stf:
        stf_findings, stf_output = run_stf_checks(
            docs_dir=docs_dir,
            stf_script=stf_script,
        )
        findings.extend(stf_findings)

    if strict:
        findings = [
            Finding("ERROR", f.path, f.line, f.message) if f.severity == "WARN" else f
            for f in findings
        ]

    return findings, len(md_files), stf_output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate French Diataxis structure, links, governance, and ASD-STF100 compliance."
    )
    parser.add_argument(
        "docs_dir",
        type=Path,
        help="Path to the docs/ directory to validate.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat governance warnings as errors (non-zero exit).",
    )
    parser.add_argument(
        "--check-stf",
        action="store_true",
        help="Run stf_check.py --mode procedural on non-index files under 02-guides-pratiques/.",
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
    docs_dir = args.docs_dir.resolve()
    if not docs_dir.is_dir():
        print(f"[ERROR] Documentation directory does not exist: {docs_dir}", file=sys.stderr)
        return 1

    findings, file_count, stf_output = validate_docs(
        docs_dir=docs_dir,
        strict=args.strict,
        check_stf=args.check_stf,
    )

    if stf_output:
        print(stf_output)

    for finding in findings:
        print(finding.format())

    error_count = sum(1 for item in findings if item.severity == "ERROR")
    warn_count = sum(1 for item in findings if item.severity == "WARN")
    print(
        f"Summary: {error_count} error(s), {warn_count} warning(s) across {file_count} markdown file(s)."
    )
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

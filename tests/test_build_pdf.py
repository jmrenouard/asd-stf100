"""Tests for the ASD-STF100 ReportLab specification PDF builder."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pymupdf

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_PDF_PATH = REPO_ROOT / "scripts" / "build_pdf.py"
DIST_PDF_PATH = REPO_ROOT / "dist" / "ASD-STF100_ISSUE1.pdf"

REQUIRED_TEXTS = (
    "Français Technique Simplifié",
    "Règle 5.1",
    "AVERTISSEMENT",
    "Diátaxis",
    "non-affiliation",
)


def _load_build_pdf_module():
    """Dynamically load scripts/build_pdf.py regardless of sys.path setup."""
    spec = importlib.util.spec_from_file_location("build_pdf", BUILD_PDF_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_pdf"] = module
    spec.loader.exec_module(module)
    return module


def _assert_pdf_integrity(pdf_path: Path) -> None:
    """Validate existence, size, page count, TOC outline, encoding, and content."""
    assert pdf_path.exists(), f"PDF does not exist: {pdf_path}"
    assert pdf_path.stat().st_size > 100_000, f"PDF too small: {pdf_path.stat().st_size} bytes"

    with pymupdf.open(pdf_path) as doc:
        assert doc.page_count >= 35, f"Expected >= 35 pages, got {doc.page_count}"
        toc = doc.get_toc()
        assert len(toc) > 0, "Expected non-empty PDF outline (get_toc())"

        pages_text: list[str] = []
        for idx in range(doc.page_count):
            page_text = doc[idx].get_text()
            assert "\ufffd" not in page_text, f"Replacement character U+FFFD found on page {idx + 1}"
            pages_text.append(page_text)

        full_text = "\n".join(pages_text)
        for expected in REQUIRED_TEXTS:
            assert expected in full_text, f"Missing expected French text: {expected!r}"

        # Cover page must suppress running page counter while body pages show Page X / N.
        assert "Page 1 /" not in pages_text[0]
        assert f"Page 2 / {doc.page_count}" in pages_text[1]


def test_build_pdf_generates_valid_spec(tmp_path: Path) -> None:
    """Building the specification PDF into tmp_path produces a complete, valid PDF."""
    module = _load_build_pdf_module()
    output_pdf = tmp_path / "ASD-STF100_TEST.pdf"
    result_path = module.build_pdf(output_path=output_pdf, spec_dir=REPO_ROOT / "spec")
    assert result_path == output_pdf
    _assert_pdf_integrity(output_pdf)


def test_dist_pdf_exists_and_valid() -> None:
    """Committed dist/ASD-STF100_ISSUE1.pdf exists and passes all integrity checks."""
    _assert_pdf_integrity(DIST_PDF_PATH)

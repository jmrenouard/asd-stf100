#!/usr/bin/env python3
"""Generate the publication-grade ASD-STF100 Issue 1 specification PDF.

Reads the Single Source of Truth JSON files under ``spec/`` and compiles an A4
French controlled-language specification using ReportLab and the bundled Vera
TrueType font family for complete Unicode and French accent coverage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC_DIR = REPO_ROOT / "spec"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "dist" / "ASD-STF100_ISSUE1.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LR = 20 * mm
MARGIN_TB = 22 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN_LR  # 170 mm
CONTENT_HEIGHT = PAGE_HEIGHT - 2 * MARGIN_TB  # 253 mm

# Institutional color palette.
NAVY = colors.HexColor("#0F172A")
SLATE_DARK = colors.HexColor("#1E293B")
SLATE_TEXT = colors.HexColor("#334155")
SLATE_MUTED = colors.HexColor("#64748B")
BORDER_SLATE = colors.HexColor("#CBD5E1")
SURFACE_SLATE = colors.HexColor("#F8FAFC")
SURFACE_ALT = colors.HexColor("#F1F5F9")
CYAN_ACCENT = colors.HexColor("#0284C7")
CYAN_LIGHT = colors.HexColor("#38BDF8")
CYAN_PALE = colors.HexColor("#7DD3FC")
CYAN_SOFT = colors.HexColor("#E0F2FE")

GREEN_DARK = colors.HexColor("#14532D")
GREEN_HEADER = colors.HexColor("#166534")
GREEN_SOFT = colors.HexColor("#DCFCE7")
GREEN_BORDER = colors.HexColor("#86EFAC")

AMBER_DARK = colors.HexColor("#92400E")
AMBER_SOFT = colors.HexColor("#FEF3C7")
AMBER_BORDER = colors.HexColor("#FCD34D")

RED_DARK = colors.HexColor("#991B1B")
RED_SOFT = colors.HexColor("#FEE2E2")
RED_BORDER = colors.HexColor("#FCA5A5")

# Symbol substitutions for glyphs absent from Bitstream Vera.
SYMBOL_FALLBACKS = {
    "\u202f": "\u00a0",  # Narrow no-break space -> standard NBSP.
    "\u2009": " ",       # Thin space -> regular space.
    "\u2011": "-",       # Non-breaking hyphen -> ASCII hyphen.
    "\u2192": "->",      # Right arrow.
    "\u2190": "<-",      # Left arrow.
    "\u2194": "<->",     # Left-right arrow.
    "\u21d2": "=>",      # Double right arrow.
    "\u2713": "[OK]",    # Check mark.
    "\u2714": "[OK]",    # Heavy check mark.
    "\u2717": "[X]",     # Ballot X.
    "\u2718": "[X]",     # Heavy ballot X.
}

_VERA_CMAP: set[int] | None = None


def register_vera_fonts() -> set[int]:
    """Register the Vera TrueType font family and return supported codepoints."""
    global _VERA_CMAP
    fonts_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    font_files = {
        "Vera": fonts_dir / "Vera.ttf",
        "VeraBd": fonts_dir / "VeraBd.ttf",
        "VeraIt": fonts_dir / "VeraIt.ttf",
        "VeraBI": fonts_dir / "VeraBI.ttf",
    }
    for font_name, font_path in font_files.items():
        if not font_path.exists():
            raise FileNotFoundError(f"Required ReportLab font missing: {font_path}")
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

    pdfmetrics.registerFontFamily(
        "Vera",
        normal="Vera",
        bold="VeraBd",
        italic="VeraIt",
        boldItalic="VeraBI",
    )

    if _VERA_CMAP is None:
        base_font = TTFont("Vera", str(font_files["Vera"]))
        _VERA_CMAP = set(base_font.face.charToGlyph.keys())
    return _VERA_CMAP


def sanitize_text(text: str) -> str:
    """Normalize text so every character renders cleanly in Vera fonts."""
    if not text:
        return ""
    cmap = _VERA_CMAP if _VERA_CMAP is not None else register_vera_fonts()
    out: list[str] = []
    for ch in text:
        if ch in SYMBOL_FALLBACKS:
            out.append(SYMBOL_FALLBACKS[ch])
        elif ch in ("\n", "\r", "\t") or ord(ch) in cmap:
            out.append(ch)
        else:
            out.append(" ")
    return "".join(out)


def p_esc(text: str) -> str:
    """Sanitize and XML-escape plain text for ReportLab Paragraph markup."""
    return escape(sanitize_text(text))


def slug_key(prefix: str, index: int, title: str) -> str:
    """Build a deterministic, ReportLab-safe bookmark key."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_")[:32]
    return f"{prefix}_{index}_{clean}"


def build_styles() -> dict[str, ParagraphStyle]:
    """Create the complete typography style dictionary using Vera."""
    return {
        "CoverBadge": ParagraphStyle(
            "CoverBadge",
            fontName="VeraBd",
            fontSize=9,
            leading=12,
            textColor=CYAN_PALE,
            spaceAfter=6,
        ),
        "CoverCode": ParagraphStyle(
            "CoverCode",
            fontName="VeraBd",
            fontSize=34,
            leading=40,
            textColor=colors.white,
            spaceAfter=6,
        ),
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            fontName="VeraBd",
            fontSize=19,
            leading=24,
            textColor=CYAN_PALE,
            spaceAfter=6,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName="VeraIt",
            fontSize=11.5,
            leading=16,
            textColor=colors.HexColor("#E2E8F0"),
            spaceAfter=10,
        ),
        "CoverLead": ParagraphStyle(
            "CoverLead",
            fontName="Vera",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#CBD5E1"),
        ),
        "CoverCardHeading": ParagraphStyle(
            "CoverCardHeading",
            fontName="VeraBd",
            fontSize=11,
            leading=15,
            textColor=NAVY,
            spaceAfter=4,
        ),
        "CoverCardBody": ParagraphStyle(
            "CoverCardBody",
            fontName="Vera",
            fontSize=9.5,
            leading=13.5,
            textColor=SLATE_TEXT,
        ),
        "CoverMetaLabel": ParagraphStyle(
            "CoverMetaLabel",
            fontName="VeraBd",
            fontSize=8.5,
            leading=12,
            textColor=NAVY,
        ),
        "CoverMetaVal": ParagraphStyle(
            "CoverMetaVal",
            fontName="Vera",
            fontSize=8.5,
            leading=12,
            textColor=SLATE_TEXT,
        ),
        "PartBanner": ParagraphStyle(
            "PartBanner",
            fontName="VeraBd",
            fontSize=9,
            leading=12,
            textColor=CYAN_ACCENT,
            spaceBefore=2,
            spaceAfter=2,
        ),
        "H1": ParagraphStyle(
            "H1",
            fontName="VeraBd",
            fontSize=16,
            leading=21,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "H2": ParagraphStyle(
            "H2",
            fontName="VeraBd",
            fontSize=12.5,
            leading=17,
            textColor=CYAN_ACCENT,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "H3": ParagraphStyle(
            "H3",
            fontName="VeraBd",
            fontSize=10.5,
            leading=14,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName="Vera",
            fontSize=9.5,
            leading=14,
            textColor=SLATE_TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        ),
        "BodyLeft": ParagraphStyle(
            "BodyLeft",
            fontName="Vera",
            fontSize=9.5,
            leading=13.5,
            textColor=SLATE_TEXT,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            fontName="Vera",
            fontSize=9.3,
            leading=13.5,
            textColor=SLATE_TEXT,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        ),
        "CodeBlock": ParagraphStyle(
            "CodeBlock",
            fontName="Vera",
            fontSize=8.2,
            leading=11.5,
            textColor=NAVY,
            backColor=SURFACE_ALT,
            leftIndent=6,
            rightIndent=6,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            fontName="VeraBd",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "TableHeaderAmber": ParagraphStyle(
            "TableHeaderAmber",
            fontName="VeraBd",
            fontSize=8.5,
            leading=11.5,
            textColor=AMBER_DARK,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "TableHeaderGreen": ParagraphStyle(
            "TableHeaderGreen",
            fontName="VeraBd",
            fontSize=8.5,
            leading=11.5,
            textColor=GREEN_HEADER,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            fontName="Vera",
            fontSize=8.3,
            leading=11.5,
            textColor=SLATE_TEXT,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            fontName="VeraBd",
            fontSize=8.3,
            leading=11.5,
            textColor=NAVY,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "DictWordApproved": ParagraphStyle(
            "DictWordApproved",
            fontName="VeraBd",
            fontSize=8.2,
            leading=11,
            textColor=NAVY,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "DictWordUnapproved": ParagraphStyle(
            "DictWordUnapproved",
            fontName="VeraIt",
            fontSize=8.2,
            leading=11,
            textColor=AMBER_DARK,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "DictCell": ParagraphStyle(
            "DictCell",
            fontName="Vera",
            fontSize=8.0,
            leading=10.8,
            textColor=SLATE_TEXT,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "DictCellStf": ParagraphStyle(
            "DictCellStf",
            fontName="Vera",
            fontSize=8.0,
            leading=10.8,
            textColor=GREEN_DARK,
            alignment=TA_LEFT,
            splitLongWords=1,
        ),
        "RuleTitle": ParagraphStyle(
            "RuleTitle",
            fontName="VeraBd",
            fontSize=10,
            leading=13.5,
            textColor=NAVY,
        ),
        "RuleStatement": ParagraphStyle(
            "RuleStatement",
            fontName="VeraBd",
            fontSize=9.2,
            leading=13,
            textColor=SLATE_DARK,
            spaceAfter=3,
        ),
        "RuleExplain": ParagraphStyle(
            "RuleExplain",
            fontName="Vera",
            fontSize=9.0,
            leading=12.8,
            textColor=SLATE_TEXT,
        ),
        "CalloutTitle": ParagraphStyle(
            "CalloutTitle",
            fontName="VeraBd",
            fontSize=9.5,
            leading=13,
            textColor=NAVY,
            spaceAfter=2,
        ),
        "CalloutBody": ParagraphStyle(
            "CalloutBody",
            fontName="Vera",
            fontSize=9.0,
            leading=12.5,
            textColor=SLATE_TEXT,
        ),
        "TocTitle": ParagraphStyle(
            "TocTitle",
            fontName="VeraBd",
            fontSize=16,
            leading=21,
            textColor=NAVY,
            spaceAfter=8,
        ),
        "TOC0": ParagraphStyle(
            "TOC0",
            fontName="VeraBd",
            fontSize=9.8,
            leading=14,
            textColor=NAVY,
            leftIndent=0,
            firstLineIndent=0,
            rightIndent=16 * mm,
            spaceBefore=5,
            spaceAfter=1,
        ),
        "TOC1": ParagraphStyle(
            "TOC1",
            fontName="Vera",
            fontSize=8.8,
            leading=12.5,
            textColor=SLATE_TEXT,
            leftIndent=12,
            firstLineIndent=0,
            rightIndent=16 * mm,
            spaceBefore=1,
            spaceAfter=1,
        ),
        "QuadCellTitle": ParagraphStyle(
            "QuadCellTitle",
            fontName="VeraBd",
            fontSize=9.2,
            leading=12.5,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
    }


class SpecDocTemplate(BaseDocTemplate):
    """ReportLab BaseDocTemplate tracking total pages and PDF bookmarks."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.known_total_pages = 0
        self._pass_pages = 0
        self._bookmark_counter = 0

    def handle_documentBegin(self) -> None:
        super().handle_documentBegin()
        self._pass_pages = 0
        self._bookmark_counter = 0

    def afterPage(self) -> None:
        self._pass_pages = self.page
        super().afterPage()

    def _allSatisfied(self) -> bool:
        satisfied = super()._allSatisfied()
        if self._pass_pages != self.known_total_pages:
            self.known_total_pages = self._pass_pages
            return False
        return satisfied

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in ("H1", "H2"):
            return
        level = 0 if style_name == "H1" else 1
        plain_text = sanitize_text(flowable.getPlainText()).strip()
        if not plain_text:
            return
        self._bookmark_counter += 1
        key = slug_key("sec", self._bookmark_counter, plain_text)
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(plain_text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, escape(plain_text), self.page, key))


def draw_cover_backdrop(canv, _doc) -> None:
    """Draw the institutional navy/cyan cover page backdrop on page 1."""
    canv.saveState()

    # Upper institutional navy banner (top 148 mm of page).
    hero_bottom = 148 * mm
    canv.setFillColor(NAVY)
    canv.rect(0, hero_bottom, PAGE_WIDTH, PAGE_HEIGHT - hero_bottom, stroke=0, fill=1)

    # Subtle geometric accent grid lines in top-right of hero banner.
    canv.setStrokeColor(SLATE_DARK)
    canv.setLineWidth(0.75)
    for offset in range(0, 60, 12):
        canv.line(145 * mm + offset * mm, hero_bottom, PAGE_WIDTH, hero_bottom + (65 - offset) * mm)

    # Horizontal cyan divider under hero banner.
    canv.setFillColor(CYAN_ACCENT)
    canv.rect(0, hero_bottom - 2.5 * mm, PAGE_WIDTH, 2.5 * mm, stroke=0, fill=1)

    # Full-height left architectural cyan bar.
    canv.setFillColor(CYAN_ACCENT)
    canv.rect(0, 0, 7 * mm, PAGE_HEIGHT, stroke=0, fill=1)

    # Bottom institutional footer band.
    canv.setFillColor(NAVY)
    canv.rect(0, 0, PAGE_WIDTH, 16 * mm, stroke=0, fill=1)
    canv.setFont("Vera", 8)
    canv.setFillColor(colors.HexColor("#CBD5E1"))
    canv.drawString(
        MARGIN_LR,
        6.5 * mm,
        sanitize_text("ASD-STF100 — Spécification ouverte • Licences MIT (code) / CC-BY-SA-4.0 (texte)"),
    )
    canv.drawRightString(PAGE_WIDTH - MARGIN_LR, 6.5 * mm, "Édition 1.0")

    canv.restoreState()


def draw_body_chrome(canv, doc: SpecDocTemplate) -> None:
    """Draw running headers and footers on content pages (suppressed on page 1)."""
    if doc.page <= 1:
        return
    canv.saveState()

    # Running header.
    header_y = PAGE_HEIGHT - 13 * mm
    canv.setFont("VeraBd", 8)
    canv.setFillColor(NAVY)
    canv.drawString(MARGIN_LR, header_y, sanitize_text("ASD-STF100 — Français Technique Simplifié"))

    canv.setFont("Vera", 8)
    canv.setFillColor(SLATE_MUTED)
    canv.drawRightString(PAGE_WIDTH - MARGIN_LR, header_y, sanitize_text("Édition 1.0"))

    canv.setStrokeColor(CYAN_ACCENT)
    canv.setLineWidth(0.6)
    canv.line(MARGIN_LR, header_y - 3 * mm, PAGE_WIDTH - MARGIN_LR, header_y - 3 * mm)

    # Running footer.
    footer_y = 12 * mm
    canv.setStrokeColor(BORDER_SLATE)
    canv.setLineWidth(0.5)
    canv.line(MARGIN_LR, footer_y + 4.5 * mm, PAGE_WIDTH - MARGIN_LR, footer_y + 4.5 * mm)

    canv.setFont("Vera", 8)
    canv.setFillColor(SLATE_MUTED)
    canv.drawString(MARGIN_LR, footer_y, "github.com/jmrenouard/asd-stf100")

    total = doc.known_total_pages or doc.page
    canv.setFont("VeraBd", 8)
    canv.setFillColor(NAVY)
    canv.drawRightString(PAGE_WIDTH - MARGIN_LR, footer_y, f"Page {doc.page} / {total}")

    canv.restoreState()


def load_spec_data(spec_dir: Path) -> tuple[dict, dict, dict]:
    """Load rules.json, categories.json, and dictionary.json with UTF-8 encoding."""
    rules_path = spec_dir / "rules.json"
    categories_path = spec_dir / "categories.json"
    dict_path = spec_dir / "dictionary.json"

    for path in (rules_path, categories_path, dict_path):
        if not path.exists():
            raise FileNotFoundError(f"Required specification file missing: {path}")

    rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
    categories_data = json.loads(categories_path.read_text(encoding="utf-8"))
    dict_data = json.loads(dict_path.read_text(encoding="utf-8"))
    return rules_data, categories_data, dict_data


def make_styled_table(
    rows: list[list],
    col_widths: list[float],
    header_bg=NAVY,
    repeat_rows: int = 1,
    zebra: bool = True,
) -> Table:
    """Create a bordered ReportLab Table with optional repeating header and zebra striping."""
    table = Table(rows, colWidths=col_widths, repeatRows=repeat_rows)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER_SLATE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if zebra and len(rows) > 2:
        for row_idx in range(1, len(rows)):
            if row_idx % 2 == 0:
                commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), SURFACE_SLATE))
    table.setStyle(TableStyle(commands))
    return table


def make_comparison_table(
    examples: list[dict],
    styles: dict[str, ParagraphStyle],
) -> Table | None:
    """Build a styled Non-STF vs STF comparison table from rule/GR examples."""
    if not examples:
        return None
    col_w = [CONTENT_WIDTH * 0.48, CONTENT_WIDTH * 0.52]
    rows: list[list] = [
        [
            Paragraph("<b>Non-STF (à éviter)</b>", styles["TableHeaderAmber"]),
            Paragraph("<b>STF (conforme)</b>", styles["TableHeaderGreen"]),
        ]
    ]
    commands = [
        ("BACKGROUND", (0, 0), (0, 0), AMBER_SOFT),
        ("BACKGROUND", (1, 0), (1, 0), GREEN_SOFT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, BORDER_SLATE),
        ("LINEBELOW", (0, 0), (0, 0), 1.0, AMBER_BORDER),
        ("LINEBELOW", (1, 0), (1, 0), 1.0, GREEN_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    for ex in examples:
        row_idx = len(rows)
        non_stf = ex.get("non_stf", "").strip() or "—"
        stf = ex.get("stf", "").strip() or "—"
        note = ex.get("note", "").strip()
        rows.append(
            [
                Paragraph(p_esc(non_stf), styles["TableCell"]),
                Paragraph(p_esc(stf), styles["TableCell"]),
            ]
        )
        commands.append(("BACKGROUND", (0, row_idx), (0, row_idx), colors.HexColor("#FFFBEB")))
        commands.append(("BACKGROUND", (1, row_idx), (1, row_idx), colors.HexColor("#F0FDF4")))
        if note:
            note_idx = len(rows)
            rows.append(
                [
                    Paragraph(f"<i>Note : {p_esc(note)}</i>", styles["TableCell"]),
                    "",
                ]
            )
            commands.append(("SPAN", (0, note_idx), (1, note_idx)))
            commands.append(("BACKGROUND", (0, note_idx), (1, note_idx), SURFACE_SLATE))
            commands.append(("NOSPLIT", (0, row_idx), (-1, note_idx)))

    table = Table(rows, colWidths=col_w, repeatRows=1)
    table.setStyle(TableStyle(commands))
    return table


def make_code_box(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    """Wrap preformatted CLI or directory-tree text in a styled slate container."""
    pre = Preformatted(sanitize_text(text), styles["CodeBlock"])
    box = Table([[pre]], colWidths=[CONTENT_WIDTH])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE_ALT),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_SLATE),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, SLATE_MUTED),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return box


def make_callout_box(
    title: str,
    body_lines: list[str],
    styles: dict[str, ParagraphStyle],
    bg_color=SURFACE_SLATE,
    accent_color=CYAN_ACCENT,
    border_color=BORDER_SLATE,
) -> Table:
    """Build a left-accented callout box for warnings, cautions, or notes."""
    content = [Paragraph(p_esc(title), styles["CalloutTitle"])]
    for line in body_lines:
        content.append(Paragraph(p_esc(line), styles["CalloutBody"]))
    table = Table([[content]], colWidths=[CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                ("LINEBEFORE", (0, 0), (0, -1), 3.0, accent_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def append_cover_page(story: list, rules_data: dict, dict_data: dict, categories_data: dict, styles: dict[str, ParagraphStyle]) -> None:
    """Append page 1 cover page flowables aligned with the navy/cyan backdrop."""
    meta = rules_data.get("meta", {})
    sections = rules_data.get("sections", [])
    rule_count = sum(len(sec.get("rules", [])) for sec in sections)
    gr_count = len(rules_data.get("general_recommendations", []))
    noun_cats = len(categories_data.get("technical_noun_categories", []))
    verb_cats = len(categories_data.get("technical_verb_categories", []))
    entries = dict_data.get("entries", [])
    approved_count = sum(1 for entry in entries if entry.get("approved"))

    # Hero block fixed inside the upper navy region (120 mm tall).
    hero_content = [
        Paragraph("NORME OUVERTE • ÉDITION 1.0 • NOVEMBRE 2026", styles["CoverBadge"]),
        Paragraph(p_esc(meta.get("code", "ASD-STF100")), styles["CoverCode"]),
        Paragraph(p_esc(meta.get("title", "Français Technique Simplifié")), styles["CoverTitle"]),
        Paragraph(
            p_esc("Norme ouverte de rédaction technique contrôlée"),
            styles["CoverSubtitle"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            p_esc(
                "Spécification complète pour la rédaction de procédures d'exploitation, "
                "guides pratiques, consignes de sécurité et documentation technique "
                "automatisée (Diátaxis FR & Docs-as-Code)."
            ),
            styles["CoverLead"],
        ),
    ]
    hero_table = Table([[hero_content]], colWidths=[CONTENT_WIDTH], rowHeights=[120 * mm])
    hero_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(hero_table)
    story.append(Spacer(1, 14 * mm))

    # Slate institutional summary card in the lower light region.
    card_inner = [
        Paragraph("Périmètre normatif et outillage", styles["CoverCardHeading"]),
        Paragraph(
            p_esc(
                f"• {rule_count} règles de rédaction contrôlée réparties en 9 sections "
                f"et {gr_count} recommandations générales (GR-1 à GR-8)."
            ),
            styles["CoverCardBody"],
        ),
        Paragraph(
            p_esc(
                f"• {noun_cats} catégories de noms techniques et {verb_cats} catégories "
                f"de verbes techniques pour les domaines industriels et numériques."
            ),
            styles["CoverCardBody"],
        ),
        Paragraph(
            p_esc(
                f"• Dictionnaire contrôlé A–Z ({len(entries)} entrées dont {approved_count} "
                "mots approuvés) et vérificateur automatique stf_check.py."
            ),
            styles["CoverCardBody"],
        ),
        Paragraph(
            p_esc(
                "• Architecture documentaire Diátaxis (FR) et chaîne Docs-as-Code "
                "(MkDocs Material, Vale, markdownlint, CI/CD)."
            ),
            styles["CoverCardBody"],
        ),
    ]
    slate_card = Table([[card_inner]], colWidths=[CONTENT_WIDTH])
    slate_card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE_SLATE),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER_SLATE),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, CYAN_ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(slate_card)
    story.append(Spacer(1, 8 * mm))

    # Publication metadata grid.
    meta_rows = [
        [
            Paragraph("Édition", styles["CoverMetaLabel"]),
            Paragraph("Édition 1.0 — Novembre 2026", styles["CoverMetaVal"]),
        ],
        [
            Paragraph("Licences Open-Source", styles["CoverMetaLabel"]),
            Paragraph("MIT (logiciels, linter, skills) / CC-BY-SA-4.0 (spécification)", styles["CoverMetaVal"]),
        ],
        [
            Paragraph("Dépôt officiel", styles["CoverMetaLabel"]),
            Paragraph(p_esc(meta.get("repository", "https://github.com/jmrenouard/asd-stf100")), styles["CoverMetaVal"]),
        ],
        [
            Paragraph("Filiation méthodologique", styles["CoverMetaLabel"]),
            Paragraph(
                "Inspirée d'ASD-STE100 Issue 9 (sans affiliation avec ASD)",
                styles["CoverMetaVal"],
            ),
        ],
    ]
    meta_table = Table(meta_rows, colWidths=[45 * mm, CONTENT_WIDTH - 45 * mm])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER_SLATE),
                ("BACKGROUND", (0, 0), (0, -1), SURFACE_ALT),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta_table)
    story.append(NextPageTemplate("Body"))
    story.append(PageBreak())


def append_legal_page(story: list, meta: dict, styles: dict[str, ParagraphStyle]) -> None:
    """Append page 2 copyright, licensing, and explicit ASD non-affiliation notice."""
    story.append(Paragraph("Mentions légales, licences et non-affiliation", styles["H1"]))

    story.append(
        make_callout_box(
            "Avis explicite de non-affiliation et reconnaissance de marque",
            [
                "ASD-STF100 (Français Technique Simplifié) est une norme ouverte et indépendante. "
                "Ce projet n'est ni affilié, ni approuvé, ni parrainé, ni certifié par "
                "l'ASD (Aerospace, Security and Defence Industries Association of Europe) "
                "ni par le STE Maintenance Group (STEMG).",
                "ASD-STE100 (Simplified Technical English) est une marque déposée de l'Union "
                "européenne appartenant à l'ASD (marque UE n° 017966390 ; enregistrement "
                "antérieur n° 004901195). La spécification officielle anglaise est publiée "
                "sur https://www.asd-ste100.org.",
            ],
            styles,
            bg_color=CYAN_SOFT,
            accent_color=CYAN_ACCENT,
            border_color=CYAN_ACCENT,
        )
    )
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Indépendance éditoriale et périmètre linguistique", styles["H3"]))
    story.append(
        Paragraph(
            p_esc(
                "Bien que la structure générale en neuf sections et la démarche de contrôle "
                "lexical s'inspirent méthodologiquement d'ASD-STE100 Issue 9 (15 janvier 2025), "
                "ASD-STF100 constitue une création linguistique originale adaptée aux règles "
                "morphosyntaxiques du français. Ce document ne reproduit aucune définition, "
                "aucun sens approuvé ni aucun exemple officiel protégé par le droit d'auteur d'ASD."
            ),
            styles["Body"],
        )
    )

    story.append(Paragraph("Régime de double licence ouverte", styles["H3"]))
    lic_rows = [
        [
            Paragraph("Composant", styles["TableHeader"]),
            Paragraph("Licence", styles["TableHeader"]),
            Paragraph("Périmètre couvert", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>Code source et outillage</b>", styles["TableCellBold"]),
            Paragraph("Licence MIT", styles["TableCell"]),
            Paragraph(
                "Vérificateur stf_check.py, outils Diátaxis FR, scripts de génération, "
                "tests automatisés et Agent Skills (src/, scripts/, tests/, skills/).",
                styles["TableCell"],
            ),
        ],
        [
            Paragraph("<b>Spécification et documentation</b>", styles["TableCellBold"]),
            Paragraph("CC-BY-SA-4.0", styles["TableCell"]),
            Paragraph(
                "Règles françaises, catégories techniques, dictionnaire contrôlé, "
                "guides Diátaxis et présent document PDF (spec/*.json, docs/, dist/).",
                styles["TableCell"],
            ),
        ],
    ]
    story.append(make_styled_table(lic_rows, [45 * mm, 32 * mm, 93 * mm]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Identification documentaire", styles["H3"]))
    id_rows = [
        [Paragraph("Champ", styles["TableHeader"]), Paragraph("Valeur", styles["TableHeader"])],
        [Paragraph("Code normatif", styles["TableCellBold"]), Paragraph(p_esc(meta.get("code", "ASD-STF100")), styles["TableCell"])],
        [Paragraph("Titre complet", styles["TableCellBold"]), Paragraph(p_esc(meta.get("title", "Français Technique Simplifié")), styles["TableCell"])],
        [Paragraph("Édition et version", styles["TableCellBold"]), Paragraph("Édition 1.0 (version 1.0.0 — Novembre 2026)", styles["TableCell"])],
        [Paragraph("Source unique de vérité", styles["TableCellBold"]), Paragraph("spec/rules.json, spec/categories.json, spec/dictionary.json", styles["TableCell"])],
        [Paragraph("Dépôt public", styles["TableCellBold"]), Paragraph(p_esc(meta.get("repository", "https://github.com/jmrenouard/asd-stf100")), styles["TableCell"])],
    ]
    story.append(make_styled_table(id_rows, [52 * mm, 118 * mm]))
    story.append(PageBreak())


def append_toc_page(story: list, styles: dict[str, ParagraphStyle]) -> None:
    """Append the dynamic Table of Contents populated across multiBuild passes."""
    story.append(Paragraph("Table des matières", styles["TocTitle"]))
    story.append(
        Paragraph(
            p_esc("Les numéros de page et les signets PDF sont générés dynamiquement lors de la compilation."),
            styles["BodyLeft"],
        )
    )
    story.append(Spacer(1, 3 * mm))

    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [styles["TOC0"], styles["TOC1"]]
    toc.tableStyle = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]
    )
    story.append(toc)
    story.append(PageBreak())


def append_introduction(story: list, styles: dict[str, ParagraphStyle]) -> None:
    """Append the general introduction covering scope, STE9 alignment, Diataxis, and CLI."""
    story.append(Paragraph("Introduction générale", styles["H1"]))

    story.append(Paragraph("1. Objectifs et champ d'application", styles["H2"]))
    story.append(
        Paragraph(
            p_esc(
                "La norme ASD-STF100 (Français Technique Simplifié) réduit les risques d'erreur "
                "humaine, d'ambiguïté grammaticale et de mauvaise interprétation dans les "
                "documents opérationnels rédigés en français. Elle s'applique aux procédures "
                "d'exploitation, aux modes opératoires de maintenance, aux runbooks d'astreinte, "
                "aux consignes de sécurité (AVERTISSEMENT et ATTENTION) ainsi qu'aux guides "
                "pratiques techniques."
            ),
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            p_esc(
                "La norme poursuit quatre objectifs mesurables : limiter la charge cognitive "
                "par des phrases courtes, imposer un vocabulaire univoque (un mot pour un sens), "
                "distinguer sans ambiguïté les instructions des descriptions, et permettre un "
                "contrôle automatisé dans les chaînes d'intégration continue (Docs-as-Code)."
            ),
            styles["Body"],
        )
    )

    story.append(Paragraph("2. Comparaison avec ASD-STE100 Issue 9", styles["H2"]))
    cmp_rows = [
        [
            Paragraph("Dimension", styles["TableHeader"]),
            Paragraph("ASD-STE100 Issue 9 (anglais)", styles["TableHeader"]),
            Paragraph("ASD-STF100 Édition 1 (français)", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>Structure</b>", styles["TableCellBold"]),
            Paragraph("9 sections de règles, 8 GR, dictionnaire contrôlé.", styles["TableCell"]),
            Paragraph("9 sections (53 règles), 8 GR, dictionnaire contrôlé A–Z.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Longueur des phrases</b>", styles["TableCellBold"]),
            Paragraph("<= 20 mots (procédural), <= 25 mots (descriptif).", styles["TableCell"]),
            Paragraph("<= 20 mots (procédural), <= 25 mots (descriptif et NOTE).", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Mode verbal procédural</b>", styles["TableCellBold"]),
            Paragraph("Impératif sans auxiliaire modal redondant.", styles["TableCell"]),
            Paragraph("Impératif présent actif (2e pluriel) ; « vous devez » interdit.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Formes en -ing / -ant</b>", styles["TableCellBold"]),
            Paragraph("9 mots approuvés en -ing hors noms techniques.", styles["TableCell"]),
            Paragraph("Gérondif (« en ...ant ») interdit ; liste fermée d'adjectifs/prépositions en -ant.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Catégories techniques</b>", styles["TableCellBold"]),
            Paragraph("22 catégories de noms, 4 catégories de verbes.", styles["TableCell"]),
            Paragraph("22 catégories de noms techniques, 4 catégories de verbes techniques.", styles["TableCell"]),
        ],
    ]
    story.append(make_styled_table(cmp_rows, [36 * mm, 66 * mm, 68 * mm]))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("3. Intégration avec Diátaxis (FR) et Docs-as-Code", styles["H2"]))
    story.append(
        Paragraph(
            p_esc(
                "ASD-STF100 s'intègre nativement avec l'architecture documentaire Diátaxis en français. "
                "Le quadrant 02-guides-pratiques/ (guides d'exploitation, déploiement, sécurité et "
                "gestion d'incidents) applique le mode procédural strict (<= 20 mots, voix active, "
                "impératif). Les quadrants 01-tutoriels/, 03-reference/ et 04-explications/ utilisent "
                "le style clair et vérifient leurs liens internes via diataxis_check_fr.py."
            ),
            styles["Body"],
        )
    )

    story.append(Paragraph("4. Vérification automatique avec stf_check.py", styles["H2"]))
    story.append(
        Paragraph(
            p_esc(
                "Le module Python asd_stf100.stf_check contrôle automatiquement les documents "
                "Markdown et le texte brut. Il isole d'abord les blocs de code, les liens URL, "
                "le frontmatter YAML et les formules LaTeX ($...$ et $$...$$), puis vérifie "
                "la longueur des phrases (avec comptage unitaire des couples nombre + unité et "
                "des mots composés), la ponctuation (interdiction du point-virgule), les verbes "
                "passifs, les modaux faibles et le dictionnaire contrôlé."
            ),
            styles["Body"],
        )
    )
    story.append(
        make_code_box(
            "python -m asd_stf100.stf_check --mode procedural docs/02-guides-pratiques/mon-runbook.md\n"
            "python -m asd_stf100.diataxis_check_fr docs --strict --check-stf",
            styles,
        )
    )
    story.append(PageBreak())


def append_categories_for_rule(
    story: list,
    rule_id: str,
    categories_data: dict,
    styles: dict[str, ParagraphStyle],
) -> None:
    """Insert the 22 noun categories under Rule 1.5 and 4 verb categories under Rule 1.12."""
    if rule_id == "1.5":
        noun_cats = categories_data.get("technical_noun_categories", [])
        story.append(Paragraph("Tableau de référence — 22 catégories de noms techniques (Règle 1.5)", styles["H3"]))
        rows = [
            [
                Paragraph("N°", styles["TableHeader"]),
                Paragraph("Catégorie", styles["TableHeader"]),
                Paragraph("Périmètre et exemples français", styles["TableHeader"]),
            ]
        ]
        for cat in noun_cats:
            examples = ", ".join(cat.get("examples", []))
            desc = cat.get("description", "").strip()
            detail = f"{desc} Exemples : {examples}" if examples else desc
            rows.append(
                [
                    Paragraph(f"<b>{cat.get('id', '')}</b>", styles["TableCellBold"]),
                    Paragraph(p_esc(cat.get("title", "")), styles["TableCellBold"]),
                    Paragraph(p_esc(detail), styles["TableCell"]),
                ]
            )
        story.append(make_styled_table(rows, [12 * mm, 52 * mm, 106 * mm]))
        story.append(Spacer(1, 5 * mm))

    elif rule_id == "1.12":
        verb_cats = categories_data.get("technical_verb_categories", [])
        story.append(Paragraph("Tableau de référence — 4 catégories de verbes techniques (Règle 1.12)", styles["H3"]))
        rows = [
            [
                Paragraph("N°", styles["TableHeader"]),
                Paragraph("Catégorie", styles["TableHeader"]),
                Paragraph("Sous-catégories et exemples", styles["TableHeader"]),
            ]
        ]
        for cat in verb_cats:
            parts: list[str] = []
            desc = cat.get("description", "").strip()
            if desc:
                parts.append(desc)
            for sub in cat.get("subcategories", []):
                sub_ex = ", ".join(sub.get("examples", []))
                parts.append(f"({sub.get('code', '')}) {sub.get('title', '')} : {sub_ex}")
            rows.append(
                [
                    Paragraph(f"<b>{cat.get('id', '')}</b>", styles["TableCellBold"]),
                    Paragraph(p_esc(cat.get("title", "")), styles["TableCellBold"]),
                    Paragraph(p_esc(" | ".join(parts)), styles["TableCell"]),
                ]
            )
        story.append(make_styled_table(rows, [12 * mm, 48 * mm, 110 * mm]))
        story.append(Spacer(1, 5 * mm))


def append_rule_block(
    story: list,
    rule_id: str,
    title: str,
    statement: str,
    explanation: str,
    examples: list[dict],
    styles: dict[str, ParagraphStyle],
    label_prefix: str = "Règle",
) -> None:
    """Render a styled rule/recommendation box and its Non-STF vs STF table."""
    header_label = f"{label_prefix} {rule_id} — {title}"
    box_rows = [
        [Paragraph(p_esc(header_label), styles["RuleTitle"])],
        [
            [
                Paragraph(f"<b>Énoncé :</b> {p_esc(statement)}", styles["RuleStatement"]),
                Paragraph(p_esc(explanation), styles["RuleExplain"]),
            ]
        ],
    ]
    rule_box = Table(box_rows, colWidths=[CONTENT_WIDTH], repeatRows=1)
    rule_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CYAN_SOFT),
                ("BACKGROUND", (0, 1), (-1, -1), SURFACE_SLATE),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_SLATE),
                ("LINEBEFORE", (0, 0), (0, -1), 3.0, CYAN_ACCENT),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, CYAN_ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    cmp_table = make_comparison_table(examples, styles)
    if cmp_table is not None and len(examples) <= 2:
        story.append(KeepTogether([rule_box, Spacer(1, 1.5 * mm), cmp_table]))
    else:
        story.append(rule_box)
        if cmp_table is not None:
            story.append(Spacer(1, 1.5 * mm))
            story.append(cmp_table)
    story.append(Spacer(1, 4.5 * mm))


def append_part1_rules(
    story: list,
    rules_data: dict,
    categories_data: dict,
    styles: dict[str, ParagraphStyle],
) -> None:
    """Append Part 1: Sections 1-9 (53 rules), categories, safety boxes, and GR-1..GR-8."""
    story.append(Paragraph("PARTIE 1", styles["PartBanner"]))
    story.append(Paragraph("Partie 1 — Règles de rédaction contrôlée", styles["H1"]))
    story.append(
        Paragraph(
            p_esc(
                "Cette partie rassemble les neuf sections normatives d'ASD-STF100 (53 règles), "
                "les listes de catégories techniques et les huit recommandations générales (GR-1 à GR-8)."
            ),
            styles["Body"],
        )
    )

    for section in rules_data.get("sections", []):
        sec_num = section.get("number")
        sec_title = section.get("title", "")
        story.append(Paragraph(p_esc(f"Section {sec_num} — {sec_title}"), styles["H2"]))
        intro = section.get("intro", "").strip()
        if intro:
            story.append(Paragraph(p_esc(intro), styles["Body"]))

        rules = section.get("rules", [])
        if rules:
            summary_rows = [
                [
                    Paragraph("Règle", styles["TableHeader"]),
                    Paragraph("Intitulé", styles["TableHeader"]),
                    Paragraph("Exigence principale", styles["TableHeader"]),
                ]
            ]
            for rule in rules:
                summary_rows.append(
                    [
                        Paragraph(f"<b>{p_esc(rule.get('id', ''))}</b>", styles["TableCellBold"]),
                        Paragraph(p_esc(rule.get("title", "")), styles["TableCellBold"]),
                        Paragraph(p_esc(rule.get("statement", "")), styles["TableCell"]),
                    ]
                )
            story.append(make_styled_table(summary_rows, [16 * mm, 52 * mm, 102 * mm]))
            story.append(Spacer(1, 4 * mm))

        if sec_num == 7:
            story.append(
                make_callout_box(
                    "AVERTISSEMENT — Modèle de consigne de sécurité (risque humain)",
                    [
                        "COUPEZ L'ALIMENTATION ÉLECTRIQUE AVANT D'OUVRIR L'ARMOIRE.",
                        "UN CONTACT DIRECT AVEC LES BARRES SOUS TENSION ENTRAÎNE UNE ÉLECTROCUTION MORTELLE.",
                    ],
                    styles,
                    bg_color=RED_SOFT,
                    accent_color=RED_DARK,
                    border_color=RED_BORDER,
                )
            )
            story.append(Spacer(1, 2.5 * mm))
            story.append(
                make_callout_box(
                    "ATTENTION — Modèle de consigne matérielle ou logicielle",
                    [
                        "SAUVEGARDEZ LA BASE DE DONNÉES AVANT D'EXÉCUTER LA MIGRATION.",
                        "UNE COUPURE PENDANT L'ÉCRITURE CORROMPT LES INDEX ET PROVOQUE UNE PERTE DE DONNÉES.",
                    ],
                    styles,
                    bg_color=AMBER_SOFT,
                    accent_color=AMBER_DARK,
                    border_color=AMBER_BORDER,
                )
            )
            story.append(Spacer(1, 4 * mm))

        for rule in rules:
            rid = rule.get("id", "")
            append_rule_block(
                story,
                rule_id=rid,
                title=rule.get("title", ""),
                statement=rule.get("statement", ""),
                explanation=rule.get("explanation", ""),
                examples=rule.get("examples", []),
                styles=styles,
                label_prefix="Règle",
            )
            append_categories_for_rule(story, rid, categories_data, styles)

    # General Recommendations (GR-1 to GR-8).
    grs = rules_data.get("general_recommendations", [])
    if grs:
        story.append(Paragraph("Recommandations générales (GR-1 à GR-8)", styles["H2"]))
        gr_summary = [
            [
                Paragraph("Code", styles["TableHeader"]),
                Paragraph("Thème", styles["TableHeader"]),
                Paragraph("Recommandation", styles["TableHeader"]),
            ]
        ]
        for gr in grs:
            gr_summary.append(
                [
                    Paragraph(f"<b>{p_esc(gr.get('id', ''))}</b>", styles["TableCellBold"]),
                    Paragraph(p_esc(gr.get("title", "")), styles["TableCellBold"]),
                    Paragraph(p_esc(gr.get("statement", "")), styles["TableCell"]),
                ]
            )
        story.append(make_styled_table(gr_summary, [18 * mm, 48 * mm, 104 * mm]))
        story.append(Spacer(1, 4 * mm))

        for gr in grs:
            append_rule_block(
                story,
                rule_id=gr.get("id", ""),
                title=gr.get("title", ""),
                statement=gr.get("statement", ""),
                explanation=gr.get("explanation", ""),
                examples=gr.get("examples", []),
                styles=styles,
                label_prefix="Recommandation",
            )

    story.append(PageBreak())


def append_part2_dictionary(story: list, dict_data: dict, styles: dict[str, ParagraphStyle]) -> None:
    """Append Part 2: guide, recurring errors, approved verbs index, and A-Z dictionary."""
    entries = dict_data.get("entries", [])
    recurring_errors = dict_data.get("recurring_errors", [])
    approved_ant = dict_data.get("meta", {}).get("approved_ant", [])

    story.append(Paragraph("PARTIE 2", styles["PartBanner"]))
    story.append(Paragraph("Partie 2 — Dictionnaire contrôlé STF-100", styles["H1"]))

    story.append(Paragraph("Guide de lecture du dictionnaire", styles["H2"]))
    story.append(
        Paragraph(
            p_esc(
                "Le dictionnaire contrôlé fixe le vocabulaire autorisé pour la rédaction "
                "procédurale et technique en français simplifié. Les mots en MAJUSCULES "
                "GRASSES sont approuvés uniquement dans la catégorie grammaticale et le sens "
                "indiqués. Les mots en minuscules italiques sont non approuvés et renvoient "
                "vers des alternatives autorisées."
            ),
            styles["Body"],
        )
    )
    guide_rows = [
        [Paragraph("Colonne / Symbole", styles["TableHeader"]), Paragraph("Signification", styles["TableHeader"])],
        [Paragraph("<b>MOT (cat.)</b>", styles["TableCellBold"]), Paragraph("Mot approuvé et catégorie : (v) verbe, (n) nom, (adj) adjectif, (adv) adverbe, (prep) préposition, (conj) conjonction, (art) article, (pron) pronom.", styles["TableCell"])],
        [Paragraph("<b>[formes]</b>", styles["TableCellBold"]), Paragraph("Formes fléchies approuvées (impératif, présent, participe passé, féminin ou pluriel régulier).", styles["TableCell"])],
        [Paragraph("<b>mot (non approuvé)</b>", styles["TableCellBold"]), Paragraph("Terme proscrit ou anglicisme, accompagné de ses ALTERNATIVES en majuscules.", styles["TableCell"])],
        [Paragraph("<b>Mots en -ant autorisés</b>", styles["TableCellBold"]), Paragraph(p_esc(", ".join(approved_ant)), styles["TableCell"])],
    ]
    story.append(make_styled_table(guide_rows, [45 * mm, 125 * mm]))
    story.append(Spacer(1, 5 * mm))

    # Recurring errors table.
    story.append(Paragraph("Tableau des erreurs récurrentes", styles["H2"]))
    story.append(
        Paragraph(
            p_esc(
                f"Les {len(recurring_errors)} correspondances suivantes corrigent les tournures "
                "lourdes, pléonasmes administratifs et anglicismes les plus fréquents."
            ),
            styles["Body"],
        )
    )
    err_rows = [
        [
            Paragraph("<b>Tournure non-STF (à proscrire)</b>", styles["TableHeaderAmber"]),
            Paragraph("<b>Remplacement STF approuvé</b>", styles["TableHeaderGreen"]),
        ]
    ]
    err_cmds = [
        ("BACKGROUND", (0, 0), (0, 0), AMBER_SOFT),
        ("BACKGROUND", (1, 0), (1, 0), GREEN_SOFT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER_SLATE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    for idx, item in enumerate(recurring_errors, start=1):
        err_rows.append(
            [
                Paragraph(p_esc(item.get("non_stf", "")), styles["TableCell"]),
                Paragraph(p_esc(item.get("stf", "")), styles["TableCellBold"]),
            ]
        )
        if idx % 2 == 0:
            err_cmds.append(("BACKGROUND", (0, idx), (-1, idx), SURFACE_SLATE))
    err_table = Table(err_rows, colWidths=[85 * mm, 85 * mm], repeatRows=1)
    err_table.setStyle(TableStyle(err_cmds))
    story.append(err_table)
    story.append(Spacer(1, 6 * mm))

    # Multi-column index of approved verbs.
    approved_verbs = sorted(
        {
            entry.get("word", "").strip().upper()
            for entry in entries
            if entry.get("approved") and entry.get("pos") == "v" and entry.get("word")
        }
    )
    story.append(Paragraph(f"Index des verbes approuvés ({len(approved_verbs)} verbes)", styles["H2"]))
    cols = 3
    per_col = (len(approved_verbs) + cols - 1) // cols if approved_verbs else 1
    verb_grid_rows = [
        [
            Paragraph("Colonne 1 (A–Z)", styles["TableHeader"]),
            Paragraph("Colonne 2", styles["TableHeader"]),
            Paragraph("Colonne 3", styles["TableHeader"]),
        ]
    ]
    for row_i in range(per_col):
        row_cells = []
        for col_i in range(cols):
            idx = col_i * per_col + row_i
            text = approved_verbs[idx] if idx < len(approved_verbs) else ""
            row_cells.append(Paragraph(f"<b>{p_esc(text)}</b>" if text else "", styles["TableCell"]))
        verb_grid_rows.append(row_cells)
    col_w3 = CONTENT_WIDTH / 3.0
    story.append(make_styled_table(verb_grid_rows, [col_w3, col_w3, col_w3]))
    story.append(PageBreak())

    # Full A-Z controlled dictionary in 4 columns summing to 170 mm.
    story.append(Paragraph(f"Dictionnaire contrôlé A–Z ({len(entries)} entrées)", styles["H2"]))
    sorted_entries = sorted(
        entries,
        key=lambda e: (str(e.get("word", "")).casefold(), str(e.get("pos", "")).casefold()),
    )
    dict_col_widths = [34 * mm, 50 * mm, 44 * mm, 42 * mm]  # Sum = 170 mm.
    dict_rows = [
        [
            Paragraph("Mot (cat.)", styles["TableHeader"]),
            Paragraph("Sens approuvé / ALTERNATIVES", styles["TableHeader"]),
            Paragraph("EXEMPLE STF", styles["TableHeader"]),
            Paragraph("Exemple non-STF", styles["TableHeader"]),
        ]
    ]
    dict_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, BORDER_SLATE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]

    for row_idx, entry in enumerate(sorted_entries, start=1):
        word = str(entry.get("word", "")).strip()
        pos = str(entry.get("pos", "")).strip()
        approved = bool(entry.get("approved"))
        forms = entry.get("forms") or []
        meaning = str(entry.get("meaning", "")).strip()
        alternatives = entry.get("alternatives") or []
        stf_ex = str(entry.get("stf_example", "")).strip() or "—"
        non_stf_ex = str(entry.get("non_stf_example", "")).strip() or "—"

        if approved:
            head_markup = f"<b>{p_esc(word.upper())}</b> ({p_esc(pos)})"
            if forms:
                head_markup += f"<br/><font size='7' color='#475569'>[{p_esc(', '.join(forms))}]</font>"
            col1 = Paragraph(head_markup, styles["DictWordApproved"])
            col2_text = meaning or "Terme contrôlé approuvé."
            if alternatives:
                col2_text += f" | Synonymes : {', '.join(alternatives)}"
            col2 = Paragraph(p_esc(col2_text), styles["DictCell"])
            if row_idx % 2 == 0:
                dict_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), SURFACE_SLATE))
        else:
            head_markup = f"<i>{p_esc(word.lower())}</i> ({p_esc(pos)})<br/><font size='7' color='#92400E'>non approuvé</font>"
            col1 = Paragraph(head_markup, styles["DictWordUnapproved"])
            alt_str = ", ".join(str(a).upper() for a in alternatives) if alternatives else "VOIR RÈGLES"
            col2_markup = f"<b>ALTERNATIVES :</b> {p_esc(alt_str)}"
            if meaning:
                col2_markup += f"<br/>{p_esc(meaning)}"
            col2 = Paragraph(col2_markup, styles["DictCell"])
            dict_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#FFFBEB")))

        col3 = Paragraph(p_esc(stf_ex), styles["DictCellStf"])
        col4 = Paragraph(p_esc(non_stf_ex), styles["DictCell"])
        dict_rows.append([col1, col2, col3, col4])

    dict_table = Table(dict_rows, colWidths=dict_col_widths, repeatRows=1)
    dict_table.setStyle(TableStyle(dict_cmds))
    story.append(dict_table)
    story.append(PageBreak())


def append_part3_diataxis(story: list, styles: dict[str, ParagraphStyle]) -> None:
    """Append Part 3: French Diataxis documentation architecture and Docs-as-Code appendix."""
    story.append(Paragraph("PARTIE 3 — ANNEXE", styles["PartBanner"]))
    story.append(
        Paragraph("Partie 3 — Annexe : Architecture documentaire Diátaxis (FR) & Docs-as-Code", styles["H1"])
    )

    story.append(Paragraph("1. Matrice à deux axes et quatre quadrants", styles["H2"]))
    story.append(
        Paragraph(
            p_esc(
                "Le modèle Diátaxis classe toute documentation technique selon deux axes "
                "orthogonaux : l'orientation (acquisition de compétences vs exploitation) et "
                "le registre (pratique vs théorique). Règle d'or : ne jamais mélanger deux "
                "quadrants sur une même page."
            ),
            styles["Body"],
        )
    )

    matrix_rows = [
        [
            Paragraph("Axe", styles["TableHeader"]),
            Paragraph("Étude / Apprentissage", styles["TableHeader"]),
            Paragraph("Travail / Exploitation", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>Pratique (Action)</b>", styles["TableCellBold"]),
            Paragraph(
                "<b>01 — Tutoriels (01-tutoriels/)</b><br/>"
                "Apprentissage guidé pas à pas dans un environnement isolé et reproductible.",
                styles["TableCell"],
            ),
            Paragraph(
                "<b>02 — Guides pratiques (02-guides-pratiques/)</b><br/>"
                "Procédures ciblées et runbooks d'astreinte rédigés en <b>ASD-STF100 strict</b>.",
                styles["TableCell"],
            ),
        ],
        [
            Paragraph("<b>Théorie (Connaissance)</b>", styles["TableCellBold"]),
            Paragraph(
                "<b>04 — Explications (04-explications/)</b><br/>"
                "Vues d'architecture, arbitrages techniques (ADR) et fonctionnement interne.",
                styles["TableCell"],
            ),
            Paragraph(
                "<b>03 — Référence (03-reference/)</b><br/>"
                "Spécifications sèches, tables de paramètres, codes d'erreur, ports et CLI.",
                styles["TableCell"],
            ),
        ],
    ]
    story.append(make_styled_table(matrix_rows, [32 * mm, 69 * mm, 69 * mm]))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("2. Arborescence canonique française (docs/)", styles["H2"]))
    tree_text = (
        "docs/\n"
        "|-- index.md\n"
        "|-- assets/\n"
        "|   |-- architecture/\n"
        "|   +-- runbooks/\n"
        "|-- 01-tutoriels/  [Apprendre par un lab reproductible]\n"
        "|   +-- index.md\n"
        "|-- 02-guides-pratiques/  [Agir — ASD-STF100 strict <= 20 mots]\n"
        "|   |-- index.md\n"
        "|   |-- deploiement/\n"
        "|   |-- exploitation/\n"
        "|   |-- gestion-incidents/\n"
        "|   +-- securite/\n"
        "|-- 03-reference/  [Vérifier des faits neutres]\n"
        "|   |-- index.md\n"
        "|   |-- architecture-specs/\n"
        "|   |-- configuration/\n"
        "|   |-- cli-et-scripts/\n"
        "|   +-- codes-erreurs/\n"
        "+-- 04-explications/  [Comprendre les choix et mécanismes]\n"
        "    |-- index.md\n"
        "    |-- vue-architecture/\n"
        "    |-- decisions-architecture/  [ADR]\n"
        "    +-- analyses-internes/"
    )
    story.append(make_code_box(tree_text, styles))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("3. Tableau des garde-fous par quadrant", styles["H2"]))
    guard_rows = [
        [
            Paragraph("Quadrant", styles["TableHeader"]),
            Paragraph("Ton et style", styles["TableHeader"]),
            Paragraph("À inclure", styles["TableHeader"]),
            Paragraph("À proscrire", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>01-tutoriels/</b>", styles["TableCellBold"]),
            Paragraph("Pédagogique et encourageant", styles["TableCell"]),
            Paragraph("Prérequis isolés, commandes exactes, résultats attendus", styles["TableCell"]),
            Paragraph("Options avancées, débats d'architecture, choix multiples", styles["TableCell"]),
        ],
        [
            Paragraph("<b>02-guides-pratiques/</b>", styles["TableCellBold"]),
            Paragraph("<b>ASD-STF100 strict</b> (impératif, actif)", styles["TableCell"]),
            Paragraph("Prérequis, AVERTISSEMENT/ATTENTION, étapes <= 20 mots, Vérification, Retour arrière", styles["TableCell"]),
            Paragraph("Théorie, historique, phrases > 20 mots, voix passive, modaux faibles", styles["TableCell"]),
        ],
        [
            Paragraph("<b>03-reference/</b>", styles["TableCellBold"]),
            Paragraph("Neutre, sec, factuel", styles["TableCell"]),
            Paragraph("Tableaux exhaustifs (paramètres, unités, ports, codes retour, CLI)", styles["TableCell"]),
            Paragraph("Prose narrative, tutoriels, opinions", styles["TableCell"]),
        ],
        [
            Paragraph("<b>04-explications/</b>", styles["TableCellBold"]),
            Paragraph("Analytique et discursif", styles["TableCell"]),
            Paragraph("Contexte, diagrammes, options et compromis (ADR), liens vers Référence", styles["TableCell"]),
            Paragraph("Procédures pas à pas, commandes d'exécution directe", styles["TableCell"]),
        ],
    ]
    story.append(make_styled_table(guard_rows, [33 * mm, 35 * mm, 54 * mm, 48 * mm]))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("4. Maillage inter-quadrants et chaîne Docs-as-Code", styles["H2"]))
    story.append(
        Paragraph(
            p_esc(
                "Le maillage évite toute duplication entre quadrants : chaque guide pratique ou "
                "runbook référence en en-tête la matrice d'alertes ou de paramètres dans "
                "03-reference/, et pointe en pied de page vers la vue d'architecture correspondante "
                "dans 04-explications/. Réciproquement, chaque ADR renvoie vers les valeurs exactes "
                "publiées dans 03-reference/."
            ),
            styles["Body"],
        )
    )
    toolchain_rows = [
        [
            Paragraph("Fichier / Outil", styles["TableHeader"]),
            Paragraph("Rôle dans la chaîne Docs-as-Code", styles["TableHeader"]),
        ],
        [Paragraph("<b>mkdocs.yml</b>", styles["TableCellBold"]), Paragraph("Publication statique MkDocs Material en français (language: fr) alignée sur les 4 quadrants.", styles["TableCell"])],
        [Paragraph("<b>.vale.ini & .vale/styles/STF100/</b>", styles["TableCellBold"]), Paragraph("Contrôle éditorial temps réel ciblant docs/02-guides-pratiques/ (modaux, locutions lourdes, point-virgule, abréviations latines).", styles["TableCell"])],
        [Paragraph("<b>.markdownlint.json</b>", styles["TableCellBold"]), Paragraph("Cohérence syntaxique Markdown (titres, listes, blocs de code, longueur et structure).", styles["TableCell"])],
        [Paragraph("<b>.github/workflows/docs-ci.yml</b>", styles["TableCellBold"]), Paragraph("Pipeline CI exécutant diataxis_check_fr.py --strict --check-stf, markdownlint, Vale et mkdocs build --strict.", styles["TableCell"])],
    ]
    story.append(make_styled_table(toolchain_rows, [56 * mm, 114 * mm]))


def build_pdf(output_path: Path, spec_dir: Path | None = None) -> Path:
    """Compile the full ASD-STF100 specification PDF and return the output path."""
    register_vera_fonts()
    resolved_spec_dir = spec_dir if spec_dir is not None else DEFAULT_SPEC_DIR
    rules_data, categories_data, dict_data = load_spec_data(resolved_spec_dir)
    styles = build_styles()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meta = rules_data.get("meta", {})
    doc = SpecDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=MARGIN_LR,
        rightMargin=MARGIN_LR,
        topMargin=MARGIN_TB,
        bottomMargin=MARGIN_TB,
        title=sanitize_text(f"{meta.get('code', 'ASD-STF100')} — {meta.get('title', 'Français Technique Simplifié')}"),
        author="jmrenouard / ASD-STF100 Open-Source Project",
        subject="Norme ouverte de rédaction technique contrôlée (Français Technique Simplifié)",
    )

    frame = Frame(MARGIN_LR, MARGIN_TB, CONTENT_WIDTH, CONTENT_HEIGHT, id="main_frame")
    doc.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[frame], onPage=draw_cover_backdrop),
            PageTemplate(id="Body", frames=[frame], onPage=draw_body_chrome),
        ]
    )

    story: list = []
    append_cover_page(story, rules_data, dict_data, categories_data, styles)
    append_legal_page(story, meta, styles)
    append_toc_page(story, styles)
    append_introduction(story, styles)
    append_part1_rules(story, rules_data, categories_data, styles)
    append_part2_dictionary(story, dict_data, styles)
    append_part3_diataxis(story, styles)

    doc.multiBuild(story)
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for PDF generation."""
    parser = argparse.ArgumentParser(
        description="Build the ASD-STF100 Issue 1 French specification PDF."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output PDF path (default: dist/ASD-STF100_ISSUE1.pdf).",
    )
    parser.add_argument(
        "--spec-dir",
        type=Path,
        default=DEFAULT_SPEC_DIR,
        help="Directory containing rules.json, categories.json, and dictionary.json.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    out = build_pdf(output_path=args.output, spec_dir=args.spec_dir)
    print(f"Built ASD-STF100 specification PDF: {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

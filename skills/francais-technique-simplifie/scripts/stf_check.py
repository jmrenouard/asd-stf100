#!/usr/bin/env python3
"""stf_check.py - ASD-STF100 Simplified Technical French linter.

Validates French technical prose and procedures against ASD-STF100 rules
using only the Python 3 standard library.

Usage:
    python -m asd_stf100.stf_check [--mode procedural|descriptive|mixed] [--dict PATH] [--no-vocab] [FILES...]
    python stf_check.py [--mode procedural|descriptive|mixed] [--dict PATH] [--no-vocab] [FILES...]

Exit code 0 = no errors. Exit code 1 = one or more errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ------------------------------------------------------------------ constants

LIMITS: dict[str, int] = {"procedural": 20, "descriptive": 25, "mixed": 25}

# Rule 3.5: default approved French words ending in -ant (prepositions, adjectives, nouns).
DEFAULT_APPROVED_ANT: set[str] = {
    "pendant",
    "suivant",
    "restant",
    "manquant",
    "courant",
    "existant",
    "correspondant",
    "avant",
    "devant",
    "durant",
    "concernant",
    "composant",
    "voyant",
    "lubrifiant",
    "carburant",
    "solvant",
    "isolant",
    "identifiant",
    "montant",
    "flottant",
}

# Non-verb French words ending in -ant that should not trigger Rule 3.5 gerund warnings.
# Unapproved conjunctions like "cependant" or "pourtant" are caught separately by Rule 1.1.
NON_VERB_ANT: set[str] = DEFAULT_APPROVED_ANT | {
    "maintenant",
    "auparavant",
    "autant",
    "cependant",
    "pourtant",
    "constant",
    "important",
    "suffisant",
    "puissant",
    "instant",
    "gant",
    "gants",
    "fabricant",
    "assistant",
    "enfant",
    "apparent",
    "tranchant",
    "brillant",
    "pertinent",
}

# Non-gerund nouns/prepositions that can legitimately follow "en".
EN_NON_GERUND_ANT: set[str] = {
    "avant",
    "devant",
    "courant",
    "montant",
    "composant",
    "lubrifiant",
    "carburant",
    "solvant",
    "isolant",
    "identifiant",
    "voyant",
    "instant",
}

# Words ending in -é/-i/-u that are not passive past participles.
NON_PARTICIPLE_FR: set[str] = {
    "ici",
    "ainsi",
    "aussi",
    "quasi",
    "parmi",
    "merci",
    "oui",
    "peu",
    "lieu",
    "milieu",
    "niveau",
    "tableau",
    "réseau",
    "noyau",
    "tuyau",
    "verrou",
    "trou",
    "menu",
    "tissu",
    "vertu",
    "bleu",
    "jeu",
    "feu",
    "degré",
    "fini",
}

ELISION_PREFIXES: set[str] = {"l", "d", "n", "s", "c", "j", "m", "t", "qu", "jusqu", "lorsqu", "puisqu"}

_FR_LETTER = r"A-Za-zÀ-ÖØ-öø-ÿŒœŸ"
_BOUND_LEFT = rf"(?<![{_FR_LETTER}])"
_BOUND_RIGHT = rf"(?![{_FR_LETTER}])"

# Rule 3.2: forbidden conditional verbs and hedging adverbs.
FORBIDDEN_MODALS_RE = re.compile(
    rf"{_BOUND_LEFT}(?:"
    rf"(?:devrait|devraient|pourrait|pourraient|serait|seraient|faudrait|"
    rf"éventuellement|potentiellement){_BOUND_RIGHT}|"
    rf"susceptibles?\s+(?:de{_BOUND_RIGHT}|d['’])"
    r")",
    re.IGNORECASE,
)

# Rule 5.3: redundant modal phrases in procedural instructions.
PROCEDURAL_MODALS_RE = re.compile(
    rf"{_BOUND_LEFT}(?:"
    rf"(?:vous\s+devez|il\s+faut){_BOUND_RIGHT}|"
    rf"il\s+(?:convient|est\s+nécessaire)\s+(?:de{_BOUND_RIGHT}|d['’])"
    r")",
    re.IGNORECASE,
)

# Rule 3.6: passive voice with explicit agent ("est/sont/... + participle + par").
_IRREG_PP_FR = r"(?:fait|écrit|mis|pris|compris|construit|détruit|produit|ouvert|couvert|remis|transmis)e?s?"
PASSIVE_AGENT_RE = re.compile(
    rf"{_BOUND_LEFT}(?:est|sont|était|étaient|sera|seront|a\s+été|ont\s+été)\s+"
    rf"([{_FR_LETTER}]{{2,}}[éiu]e?s?|{_IRREG_PP_FR})\s+par{_BOUND_RIGHT}",
    re.IGNORECASE,
)

# Rule 3.5: French gerund ("en + ...ant") and standalone -ant words.
GERUND_EN_RE = re.compile(
    rf"{_BOUND_LEFT}en\s+([{_FR_LETTER}]{{3,}}ant){_BOUND_RIGHT}",
    re.IGNORECASE,
)

# Rules 3.7 / 9.1 / 9.3: verbose French phrases.
VERBOSE_PHRASE_RE = re.compile(
    rf"{_BOUND_LEFT}(?:"
    rf"(?:afin|en\s+vue|dans\s+le\s+but)\s+(?:de{_BOUND_RIGHT}|d['’])|"
    rf"(?:au\s+niveau|par\s+le\s+biais|à\s+l['’]aide)\s+(?:de{_BOUND_RIGHT}|du{_BOUND_RIGHT}|des{_BOUND_RIGHT}|d['’])|"
    rf"(?:préalablement\s+à|procéder\s+à|effectuer\s+une?){_BOUND_RIGHT}"
    r")",
    re.IGNORECASE,
)

# GR-6: Latin abbreviations.
LATIN_ABBREV_RE = re.compile(
    rf"{_BOUND_LEFT}(?:e\.g\.|i\.e\.|etc\.|cf\.){_BOUND_RIGHT}",
    re.IGNORECASE,
)

# Rule 8.6.2: numbers together with units of measurement count as one word.
_UNIT_ALT = (
    r"degrés?\s+(?:Celsius|Fahrenheit|Kelvin)"
    r"|degrees?\s+(?:Celsius|Fahrenheit|Kelvin)"
    r"|°[CFK]|deg[CF]|°"
    r"|kilogrammes?|milligrammes?|grammes?|kilomètres?|centimètres?|millimètres?|micromètres?|nanomètres?|mètres?"
    r"|microsecondes?|millisecondes?|secondes?|minutes?|heures?|jours?"
    r"|litres?|millilitres?|tonnes?|pour\s+cent"
    r"|kilo-?octets?|méga-?octets?|giga-?octets?|téra-?octets?|octets?"
    r"|N·m|N-m|Nm|kN|psia|psig|psi|mbar|bar|atm|kPa|MPa|GPa|hPa|Pa"
    r"|VDC|VAC|kVA|VA|kWh|MWh|Wh|kW|MW|GW|mW|kV|mV|kA|mA|uA|µA"
    r"|GHz|MHz|kHz|Hz|kΩ|MΩ|Ω|Ω|mF|uF|µF|nF|pF|mH|kJ|MJ|dBA|dBm|dB"
    r"|Ko|Mo|Go|To|Po|KiB|MiB|GiB|TiB|Gbps|Mbps|kbps|bps|KB|MB|GB|TB|PB|bits?"
    r"|kg|mg|ug|µg|mm|cm|km|nm|um|µm|mL|ml|rpm|RPM|tr|rad"
    r"|sec|secs|min|mins|ms|us|µs|ns|ppm|ppb|px|pt|dpi|fps|FPS"
    r"|A|V|W|J|N|F|H|K|L|B|o|g|m|s|h|l|%"
)
_RATE_DENOM = r"(?:/(?:s|sec|seconde|min|minute|h|heure|jour|m|cm|mm|kg|L|l|tr))?"
NUMBER_UNIT_RE = re.compile(
    rf"(?<![{_FR_LETTER}0-9_])[+-]?\d+(?:[.,:]\d+)*(?:-[+-]?\d+(?:[.,:]\d+)*)?"
    rf"\s*(?:{_UNIT_ALT}){_RATE_DENOM}(?![{_FR_LETTER}0-9_])"
)

# Rule 8.6.4: alphanumeric label prefix such as "N° 1" or "No. 4".
ALPHANUM_ID_RE = re.compile(
    rf"{_BOUND_LEFT}[Nn](?:°|o\.)\s*\d+[A-Za-z]?(?![{_FR_LETTER}0-9_])"
)

SENT_SPLIT = re.compile(
    r"(?<!No\.)(?<!N°)(?<!Fig\.)(?<!Tab\.)(?<!Sect\.)(?<!Chap\.)"
    r"(?<!e\.g\.)(?<!i\.e\.)(?<!etc\.)(?<!cf\.)(?<=[.!?:])\s+"
    r"|(?<=etc\.)\s+(?=[A-ZÀ-ÖØ-Þ0-9])"
)

WORDISH = re.compile(
    rf"[{_FR_LETTER}0-9]+(?:[.'&/-][{_FR_LETTER}0-9]+)*"
)

VOCAB_TOKEN_RE = re.compile(
    rf"[{_FR_LETTER}]+(?:[-'’][{_FR_LETTER}]+)*"
)


# ------------------------------------------------------------------ data types


@dataclass
class DictionaryData:
    """Loaded controlled French vocabulary and unapproved word mappings."""

    approved: set[str] = field(default_factory=set)
    approved_ant: set[str] = field(default_factory=lambda: set(DEFAULT_APPROVED_ANT))
    unapproved: dict[str, tuple[str, list[str]]] = field(default_factory=dict)


@dataclass
class Report:
    """Collects STF-100 errors, warnings, and unknown vocabulary items."""

    errors: list[tuple[str, str, str]] = field(default_factory=list)
    warnings: list[tuple[str, str, str]] = field(default_factory=list)
    unknown: dict[str, int] = field(default_factory=dict)

    def error(self, loc: str, rule: str, msg: str) -> None:
        """Record a rule error."""
        self.errors.append((loc, rule, msg))

    def warn(self, loc: str, rule: str, msg: str) -> None:
        """Record a rule warning."""
        self.warnings.append((loc, rule, msg))


# ------------------------------------------------------------------ dictionary loading


def find_default_dict() -> Path | None:
    """Locate the default dictionary file for repo or standalone skill execution."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "spec" / "dictionary.json" if len(here.parents) > 2 else Path(""),
        Path.cwd() / "spec" / "dictionary.json",
        here.parent.parent / "references" / "dictionnaire-stf.md",
        Path.cwd() / "references" / "dictionnaire-stf.md",
    ]
    for cand in candidates:
        if cand and cand.is_file():
            return cand
    return None


def _register_entry_forms(
    target_approved: set[str],
    target_unapproved: dict[str, tuple[str, list[str]]],
    word: str,
    forms: list[str],
    approved: bool,
    alternatives: list[str],
) -> None:
    """Register a headword and its inflected forms into approved or unapproved lookup maps."""
    tokens = [part for part in re.split(r"[\s/]+", word.strip()) if part]
    if approved:
        target_approved.add(word.strip().lower())
        for tok in tokens:
            target_approved.add(tok.lower())
        for form in forms:
            cleaned = form.strip().lower()
            if cleaned:
                target_approved.add(cleaned)
    else:
        head_upper = word.strip().upper()
        target_unapproved.setdefault(word.strip().lower(), (head_upper, alternatives))
        for form in forms:
            cleaned = form.strip().lower()
            if cleaned:
                target_unapproved.setdefault(cleaned, (head_upper, alternatives))


def load_dictionary(path: str | Path) -> DictionaryData:
    """Load controlled vocabulary from spec/dictionary.json or dictionnaire-stf.md."""
    p = Path(path)
    data = DictionaryData()
    if p.suffix.lower() == ".json":
        payload = json.loads(p.read_text(encoding="utf-8"))
        meta_ant = payload.get("meta", {}).get("approved_ant", [])
        if meta_ant:
            data.approved_ant = {w.strip().lower() for w in meta_ant if w.strip()}
        for entry in payload.get("entries", []):
            _register_entry_forms(
                data.approved,
                data.unapproved,
                entry["word"],
                entry.get("forms", []),
                bool(entry.get("approved", True)),
                entry.get("alternatives", []),
            )
        return data

    # Parse Markdown reference table format generated by sync_docs.py.
    section = ""
    for raw_line in p.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            if "-ant" in heading:
                section = "approved_ant"
            elif "non approuvé" in heading:
                section = "unapproved"
            elif "approuvé" in heading:
                section = "approved"
            else:
                section = ""
            continue
        if not line.startswith("|") or set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        if section == "approved_ant":
            tok = cells[0].strip("` ").lower()
            if tok and tok not in {"mot", "catégorie"}:
                data.approved_ant.add(tok)
        elif section == "approved" and len(cells) >= 3:
            head = cells[0].strip("` ")
            if head.lower() in {"mot", "word"}:
                continue
            forms = [f.strip() for f in cells[2].split(",") if f.strip() and f.strip() != "—"]
            _register_entry_forms(data.approved, data.unapproved, head, forms, True, [])
        elif section == "unapproved" and len(cells) >= 4:
            head = cells[0].strip("` ")
            if head.lower() in {"mot non approuvé", "mot"}:
                continue
            forms = [f.strip() for f in cells[2].split(",") if f.strip() and f.strip() != "—"]
            alts = [a.strip() for a in cells[3].split(",") if a.strip() and a.strip() != "—"]
            _register_entry_forms(data.approved, data.unapproved, head, forms, False, alts)
    return data


# ------------------------------------------------------------------ normalization & counting


def _preserve_newlines(match: re.Match[str]) -> str:
    """Replace matched span with space plus its internal newlines to preserve line numbers."""
    return " " + "\n" * match.group(0).count("\n")


def strip_markdown(text: str) -> str:
    """Strip or mask non-controlled Markdown, code, URL, quote, comment, and math spans."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\A---\n.*?\n---(?:\n|\Z)", _preserve_newlines, text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", _preserve_newlines, text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", _preserve_newlines, text, flags=re.DOTALL)
    text = re.sub(r"~~~.*?~~~", _preserve_newlines, text, flags=re.DOTALL)
    # Mask display LaTeX math and inline code before inline LaTeX math; leave escaped \$ intact.
    text = re.sub(
        r"(?<!\\)\$\$.*?(?<!\\)\$\$",
        lambda m: " MATH " + "\n" * m.group(0).count("\n"),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"``[^`\n]+``|`[^`\n]+`", " CODE ", text)
    text = re.sub(r"(?<!\\)\$(?!\s)(?:[^\n$\\]|\\.)+?(?<!\s)\$", " MATH ", text)
    text = re.sub(r"!\[([^\]]*)\]\((?:[^()]|\([^)]*\))*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\((?:[^()]|\([^)]*\))*\)", r"\1", text)
    text = re.sub(r"https?://\S+?(?=[.,;:!?)]*(?:\s|$))", " URL ", text)
    text = re.sub(r"^[ \t]*>.*$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"\"[^\"\n]*\"|“[^”\n]*”|«[^»\n]*»", " QUOTED ", text)
    return text


def count_words(sentence: str) -> int:
    """Count words according to ASD-STF100 Section 8 rules."""
    s = sentence
    # Rule 8.5: parenthetical text counts as one word in its parent sentence.
    for _ in range(3):
        updated = re.sub(r"\([^()]*\)", " PAREN ", s)
        if updated == s:
            break
        s = updated
    # Rule 8.6.2: numbers together with units of measurement count as one word.
    s = NUMBER_UNIT_RE.sub(" NUMUNIT ", s)
    # Rule 8.6.4: alphanumeric identifiers like "N° 1" count as one word.
    s = ALPHANUM_ID_RE.sub(" ALPHANUM ", s)
    # Strip Markdown emphasis and heading markers.
    s = re.sub(r"\*\*|__|#+|\*|(?<!\w)_|_(?!\w)", " ", s)
    # Rule 8.7: hyphenated groups remain a single WORDISH token.
    return len(WORDISH.findall(s))


def iter_sentences(block: str):
    """Divide a prose block into non-empty sentences."""
    for part in SENT_SPLIT.split(block):
        part = part.strip()
        if part and WORDISH.search(part):
            yield part


def _clean_for_grammar(sent: str) -> str:
    """Remove Markdown emphasis markers and HTML entities before rule matching."""
    cleaned = re.sub(r"\*\*|__|(?<!\w)_|_(?!\w)|\*", "", sent)
    return cleaned


# ------------------------------------------------------------------ rule checks


def _warn_unapproved(
    report: Report,
    loc: str,
    raw_token: str,
    entry: tuple[str, list[str]],
) -> None:
    """Record a Rule 1.1 warning for an unapproved vocabulary token."""
    head, alts = entry
    alt_str = ", ".join(alts) if alts else "approved STF word"
    report.warn(loc, "1.1", f'unapproved word "{raw_token}": use {alt_str} (entry {head}).')


def check_vocab(text: str, report: Report, vocab: DictionaryData, loc: str) -> None:
    """Check lowercase French tokens against approved and unapproved dictionary entries."""
    for raw_token in VOCAB_TOKEN_RE.findall(text):
        if raw_token.isupper() or any(c.isupper() for c in raw_token[1:]):
            continue
        low = raw_token.lower()
        # Check exact unapproved match first (including hyphenated or elided forms).
        if low in vocab.unapproved:
            _warn_unapproved(report, loc, raw_token, vocab.unapproved[low])
            continue

        # Handle French elision prefixes (l'écran, d'erreur, qu'une, jusqu'à).
        candidates = [low]
        if "'" in low or "’" in low:
            parts = [p for p in re.split(r"['’]", low) if p]
            if len(parts) >= 2 and parts[0] in ELISION_PREFIXES:
                candidates = parts[1:]
            else:
                candidates = parts

        for tok in candidates:
            if len(tok) <= 1:
                continue
            if tok in vocab.unapproved:
                _warn_unapproved(report, loc, raw_token, vocab.unapproved[tok])
                continue
            if tok in vocab.approved or tok in vocab.approved_ant:
                continue
            if "-" in tok and all(
                (p in vocab.approved or p in vocab.approved_ant or len(p) <= 1)
                for p in tok.split("-")
                if p
            ):
                continue
            if len(tok) > 2:
                report.unknown[tok] = report.unknown.get(tok, 0) + 1


def check_sentence(
    sent: str,
    mode: str,
    report: Report,
    loc: str,
    vocab: DictionaryData | None,
) -> None:
    """Validate a single sentence against structural, grammatical, and lexical STF-100 rules."""
    limit = LIMITS[mode]
    n = count_words(sent)
    head = sent if len(sent) <= 60 else sent[:57] + "..."
    if n > 25:
        report.error(loc, "5.1/6.3", f'sentence has {n} words (max {limit}): "{head}"')
    elif n > 20:
        if mode == "procedural":
            report.error(loc, "5.1", f'sentence has {n} words (max 20): "{head}"')
        elif mode == "mixed":
            report.warn(loc, "5.1", f'sentence has {n} words (max 20 if procedural): "{head}"')

    # Rule 8.1: no semicolons (ignore HTML character entities such as &nbsp;).
    sent_no_entities = re.sub(r"&[A-Za-z]+;|&#\d+;|&#x[0-9A-Fa-f]+;", " ", sent)
    if ";" in sent_no_entities:
        report.error(loc, "8.1", f'semicolon found: "{head}". Split into two sentences.')

    clean = _clean_for_grammar(sent)

    for m in FORBIDDEN_MODALS_RE.finditer(clean):
        report.error(
            loc,
            "3.2",
            f'forbidden conditional or uncertainty word "{m.group(0)}": use direct mood or explicit condition.',
        )

    if mode == "procedural":
        for m in PROCEDURAL_MODALS_RE.finditer(clean):
            report.warn(
                loc,
                "5.3",
                f'redundant procedural modal "{m.group(0)}": use direct imperative mood.',
            )

    for m in PASSIVE_AGENT_RE.finditer(clean):
        participle = m.group(1).lower()
        if participle not in NON_PARTICIPLE_FR:
            report.error(
                loc,
                "3.6",
                f'passive voice with agent "{m.group(0)}": make the agent the subject.',
            )

    en_gerund_spans: list[tuple[int, int]] = []
    for m in GERUND_EN_RE.finditer(clean):
        word = m.group(1).lower()
        if word not in EN_NON_GERUND_ANT:
            en_gerund_spans.append(m.span(1))
            report.warn(
                loc,
                "3.5",
                f'gerund "{m.group(0)}": replace with "pendant que" or two imperative actions.',
            )

    approved_ant = vocab.approved_ant if vocab is not None else DEFAULT_APPROVED_ANT
    for m in re.finditer(rf"\b([{_FR_LETTER}]{{4,}}ant)\b", clean):
        word = m.group(1)
        lw = word.lower()
        if word.isupper():
            continue
        if any(start <= m.start(1) <= end for start, end in en_gerund_spans):
            continue
        if lw in approved_ant or lw in NON_VERB_ANT:
            continue
        if vocab is not None and lw in vocab.approved:
            continue
        report.warn(
            loc,
            "3.5",
            f'verbal -ant form "{word}": replace with a simple verb tense or approved term.',
        )

    for m in VERBOSE_PHRASE_RE.finditer(clean):
        report.warn(
            loc,
            "3.7/9.1",
            f'verbose phrase "{m.group(0)}": replace with a direct preposition or approved verb.',
        )

    for m in LATIN_ABBREV_RE.finditer(clean):
        report.warn(
            loc,
            "GR-6",
            f'Latin abbreviation "{m.group(0)}": replace with full French words.',
        )

    if vocab is not None:
        check_vocab(clean, report, vocab, loc)


def check_paragraph(
    par: str,
    mode: str,
    report: Report,
    loc: str,
    vocab: DictionaryData | None,
) -> None:
    """Validate paragraph sentence count and each contained sentence."""
    sents = list(iter_sentences(par))
    if len(sents) > 6:
        report.error(loc, "6.6", f"paragraph has {len(sents)} sentences (max 6).")
    for sent in sents:
        check_sentence(sent, mode, report, loc, vocab)


def check_text(
    text: str,
    mode: str,
    report: Report,
    name: str,
    vocab: DictionaryData | None,
) -> None:
    """Validate Markdown or plain French text against ASD-STF100 rules."""
    stripped = strip_markdown(text)
    # Remove headings, table rows, and horizontal rules while preserving line count.
    stripped = re.sub(
        r"(?m)^[ \t]*(?:#.*|\|.*|---+|\*\*\*+|___+|===+)[ \t]*$",
        "",
        stripped,
    )

    bullet = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
    lines = stripped.splitlines()
    blocks: list[tuple[int, list[str]]] = []
    cur_lines: list[str] = []
    cur_start = 1
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            if cur_lines:
                blocks.append((cur_start, cur_lines))
                cur_lines = []
        else:
            if not cur_lines:
                cur_start = idx
            cur_lines.append(line)
    if cur_lines:
        blocks.append((cur_start, cur_lines))

    for start_line, block_lines in blocks:
        par = "\n".join(block_lines).strip()
        if not par or not WORDISH.search(par):
            continue
        items: list[tuple[int, str]] = []
        prose: list[str] = []
        prose_start = start_line
        for offset, line in enumerate(block_lines):
            line_no = start_line + offset
            if bullet.match(line):
                items.append((line_no, line))
            elif items and re.match(r"^(?:  |\t)\S", line):
                prev_ln, prev_text = items[-1]
                items[-1] = (prev_ln, prev_text + " " + line.strip())
            else:
                if not prose:
                    prose_start = line_no
                prose.append(line)

        # Rule 8.4: each list item counts as its own sentence.
        for line_no, raw_item in items:
            item = bullet.sub("", raw_item, count=1)
            for sent in iter_sentences(item):
                check_sentence(sent, mode, report, f"{name}:L{line_no}", vocab)

        if prose:
            check_paragraph(
                "\n".join(prose),
                mode,
                report,
                f"{name}:L{prose_start}",
                vocab,
            )


# ------------------------------------------------------------------ CLI


def _reconfigure_utf8(*streams) -> None:
    """Ensure UTF-8 encoding on text I/O streams when running under Windows consoles."""
    for stream in streams:
        if (
            getattr(stream, "encoding", None)
            and stream.encoding.lower() not in ("utf-8", "utf8")
            and hasattr(stream, "reconfigure")
        ):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for stf_check.py."""
    _reconfigure_utf8(sys.stdout, sys.stderr)

    ap = argparse.ArgumentParser(
        description="Check French technical text against ASD-STF100 writing rules."
    )
    ap.add_argument("files", nargs="*", help="files to check (default: stdin)")
    ap.add_argument(
        "--mode",
        choices=["procedural", "descriptive", "mixed"],
        default="mixed",
        help="text mode (default: mixed)",
    )
    ap.add_argument(
        "--dict",
        dest="dict_path",
        default=None,
        help="path to dictionary.json or dictionnaire-stf.md",
    )
    ap.add_argument(
        "--no-vocab",
        action="store_true",
        help="skip controlled vocabulary checks",
    )
    args = ap.parse_args(argv)

    vocab: DictionaryData | None = None
    if not args.no_vocab:
        if args.dict_path is not None:
            dpath = Path(args.dict_path)
            if not dpath.is_file():
                print(f"ERROR   dictionary not found: {dpath}", file=sys.stderr)
                return 1
            vocab = load_dictionary(dpath)
        else:
            default_dict = find_default_dict()
            if default_dict is not None:
                vocab = load_dictionary(default_dict)

    report = Report()
    if args.files:
        for file_arg in args.files:
            path = Path(file_arg)
            if not path.is_file():
                print(f"ERROR   file not found: {path}", file=sys.stderr)
                return 1
            check_text(path.read_text(encoding="utf-8"), args.mode, report, file_arg, vocab)
    else:
        _reconfigure_utf8(sys.stdin)
        check_text(sys.stdin.read(), args.mode, report, "stdin", vocab)

    for loc, rule, msg in report.errors:
        print(f"ERROR   {loc} [rule {rule}] {msg}")
    for loc, rule, msg in report.warnings:
        print(f"WARNING {loc} [rule {rule}] {msg}")
    if report.unknown:
        words = sorted(report.unknown, key=report.unknown.get, reverse=True)
        print(f"\nCHECK   {len(words)} words are not in the approved dictionary.")
        print("        Each must be an approved technical noun (22 categories) or technical verb (4 categories):")
        for idx in range(0, len(words), 10):
            print("        " + ", ".join(words[idx : idx + 10]))

    print(f"\nResult: {len(report.errors)} errors, {len(report.warnings)} warnings.")
    if not report.errors:
        print("The text obeys the ASD-STF100 structural rules verified by this linter.")
        print("Manual review remains required to verify approved word meanings.")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())

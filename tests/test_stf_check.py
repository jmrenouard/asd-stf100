"""Unit and CLI tests for asd_stf100.stf_check."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from asd_stf100.stf_check import (
    Report,
    check_text,
    count_words,
    load_dictionary,
    main,
    strip_markdown,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_DICT = REPO_ROOT / "spec" / "dictionary.json"
SKILL_LINTER = (
    REPO_ROOT / "skills" / "francais-technique-simplifie" / "scripts" / "stf_check.py"
)


def test_strip_markdown_and_math_masking() -> None:
    """Verify frontmatter, code, URLs, quotes, and LaTeX math spans are cleanly masked."""
    doc = (
        "---\n"
        "title: Guide\n"
        "---\n"
        "# Titre ignore\n\n"
        "> Citation ignoree avec devrait;\n\n"
        "```python\n"
        "# devrait; code ignore\n"
        "```\n\n"
        "Calculez la formule $$\\sum_{i=1}^n x_i$$ puis vérifiez $k^*$ et `$HOME`.\n"
        "Consultez [le manuel](https://example.com/a(1)) et https://example.com/doc.\n"
        "Le message « Erreur fatale ; stop » coûte \\$100.\n"
        "| Col1 | Col2 |\n"
        "|---|---|\n"
        "| devrait | ; |\n"
    )
    masked = strip_markdown(doc)
    assert "title: Guide" not in masked
    assert "Citation ignoree" not in masked
    assert "code ignore" not in masked
    assert "MATH" in masked
    assert "CODE" in masked
    assert "URL" in masked
    assert "QUOTED" in masked
    assert "le manuel" in masked
    assert "\\$100" in masked

    rep = Report()
    check_text(doc, "procedural", rep, "sample.md", vocab=None)
    assert not rep.errors, f"Unexpected errors on masked content: {rep.errors}"


def test_count_words_section8_rules() -> None:
    """Verify parenthetical groups, number+unit tokens, identifiers, and hyphenated words."""
    # Rule 8.5: parenthetical text counts as one word in the parent sentence.
    assert count_words("Ouvrez la vanne (voir Section 3) avant la vidange.") == 7

    # Rule 8.6.2: numbers with units count as one word.
    assert count_words("Maintenez à 10 °C et 800 kPa pendant 15 secondes.") == 7
    assert count_words("Pesez 20 kg puis attendez 5 min ou 24 h avec 100 Mo libres.") == 10

    # Rule 8.7: hyphenated word groups count as one word.
    assert count_words("Posez le porte-outils sur le sous-système et arrêtez-le.") == 8

    # Rule 8.6.4: alphanumeric label prefix counts as one word.
    assert count_words("Ouvrez la vanne N° 1.") == 4


def test_sentence_and_paragraph_limits() -> None:
    """Verify procedural (20), descriptive (25), mixed limits and max-6-sentence paragraphs."""
    s_22 = " ".join(["mot"] * 22) + "."
    s_27 = " ".join(["mot"] * 27) + "."

    rep_proc = Report()
    check_text(s_22, "procedural", rep_proc, "t", None)
    assert any(r == "5.1" for _, r, _ in rep_proc.errors)

    rep_mixed = Report()
    check_text(s_22, "mixed", rep_mixed, "t", None)
    assert not rep_mixed.errors
    assert any(r == "5.1" for _, r, _ in rep_mixed.warnings)

    rep_desc = Report()
    check_text(s_22, "descriptive", rep_desc, "t", None)
    assert not rep_desc.errors
    assert not rep_desc.warnings

    rep_over = Report()
    check_text(s_27, "descriptive", rep_over, "t", None)
    assert any(r == "5.1/6.3" for _, r, _ in rep_over.errors)

    seven_sentences = " ".join(["Ouvrez la vanne."] * 7)
    rep_par = Report()
    check_text(seven_sentences, "descriptive", rep_par, "t", None)
    assert any(r == "6.6" for _, r, _ in rep_par.errors)


def test_grammar_and_style_rules() -> None:
    """Verify semicolons, conditionals, passive voice, gerunds, verbose phrases, and GR-6."""
    rep = Report()
    text = (
        "Coupez le disjoncteur ; ouvrez ensuite le capot.\n\n"
        "L'opérateur devrait vérifier la pression éventuellement susceptible d'augmenter.\n\n"
        "Vous devez fermer la vanne et il convient d'arrêter la pompe.\n\n"
        "La table de routage est validée par l'administrateur.\n\n"
        "Appuyez sur le bouton en maintenant le loquet en utilisant un outil.\n\n"
        "Serrez l'écrou à l'aide d'une clé afin d'éviter la fuite.\n\n"
        "Vérifiez les capteurs, e.g. la sonde, cf. annexe, etc.\n"
    )
    check_text(text, "procedural", rep, "rules.md", vocab=None)

    error_rules = {r for _, r, _ in rep.errors}
    warn_rules = {r for _, r, _ in rep.warnings}
    assert {"8.1", "3.2", "3.6"} <= error_rules
    assert {"5.3", "3.5", "3.7/9.1", "GR-6"} <= warn_rules


def test_false_positive_guards() -> None:
    """Verify non-participles, approved -ant words, and HTML entities do not trigger false positives."""
    vocab = load_dictionary(SPEC_DICT)
    rep = Report()
    clean_text = (
        "Ouvrez l'armoire pendant le cycle suivant.\n\n"
        "Le voyant courant reste allumé devant le composant isolant.\n\n"
        "Le fichier est ici par conception&nbsp;et reste valide.\n"
    )
    check_text(clean_text, "descriptive", rep, "ok.md", vocab)
    assert not rep.errors, rep.errors
    assert not rep.warnings, rep.warnings


def test_dictionary_checks_and_elisions() -> None:
    """Verify unapproved words warn with alternatives and French elisions pass cleanly."""
    vocab = load_dictionary(SPEC_DICT)
    rep = Report()
    check_text(
        "Effectuez une vérification puis rebootez l'écran d'accueil.",
        "procedural",
        rep,
        "vocab.md",
        vocab,
    )
    assert not rep.errors
    warn_msgs = "\n".join(msg for _, _, msg in rep.warnings)
    assert "Effectuez" in warn_msgs
    assert "rebootez" in warn_msgs
    assert "l" not in rep.unknown
    assert "d" not in rep.unknown


def test_cli_exit_codes_and_standalone_skill(tmp_path: Path, capsys) -> None:
    """Verify module CLI, stdin mode, --no-vocab, and standalone skill execution."""
    ok_file = tmp_path / "ok.md"
    ok_file.write_text("Coupez l'alimentation. Ouvrez ensuite le capot.\n", encoding="utf-8")
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("L'équipe devrait redémarrer le serveur ; puis attendre.\n", encoding="utf-8")

    assert main(["--mode", "procedural", str(ok_file)]) == 0
    assert main(["--mode", "procedural", "--no-vocab", str(ok_file)]) == 0
    assert main(["--mode", "procedural", str(bad_file)]) == 1
    assert main([str(tmp_path / "missing.md")]) == 1
    assert main(["--dict", str(tmp_path / "missing.json"), str(ok_file)]) == 1
    capsys.readouterr()

    # Subprocess stdin test for module CLI.
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    res_mod = subprocess.run(
        [sys.executable, "-m", "asd_stf100.stf_check", "--mode", "procedural"],
        input="Coupez le disjoncteur principal.\n",
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res_mod.returncode == 0, res_mod.stdout + res_mod.stderr

    # Standalone skill execution must resolve ../references/dictionnaire-stf.md automatically.
    res_skill_ok = subprocess.run(
        [sys.executable, str(SKILL_LINTER), "--mode", "procedural", str(ok_file)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res_skill_ok.returncode == 0, res_skill_ok.stdout + res_skill_ok.stderr

    res_skill_bad = subprocess.run(
        [sys.executable, str(SKILL_LINTER), "--mode", "procedural", str(bad_file)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res_skill_bad.returncode == 1

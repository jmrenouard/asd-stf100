"""Integrity tests for ASD-STF100 specification JSONs and sync_docs.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from asd_stf100.stf_check import Report, check_text, load_dictionary

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = REPO_ROOT / "spec"


def _load_json(name: str) -> dict:
    return json.loads((SPEC_DIR / name).read_text(encoding="utf-8"))


def test_rules_json_completeness() -> None:
    """Verify rules.json covers all 9 sections, 53 rules, and 8 general recommendations."""
    data = _load_json("rules.json")
    meta = data["meta"]
    assert meta["code"] == "ASD-STF100"
    assert meta["license_code"] == "MIT"
    assert meta["license_spec"] == "CC-BY-SA-4.0"

    sections = data["sections"]
    assert [s["number"] for s in sections] == list(range(1, 10))

    expected_counts = {1: 14, 2: 2, 3: 7, 4: 5, 5: 5, 6: 6, 7: 3, 8: 7, 9: 4}
    all_rule_ids: list[str] = []
    for sec in sections:
        num = sec["number"]
        rules = sec["rules"]
        assert len(rules) == expected_counts[num], f"Section {num} count mismatch"
        assert sec["title"].strip()
        assert sec["intro"].strip()
        for idx, rule in enumerate(rules, start=1):
            assert rule["id"] == f"{num}.{idx}"
            assert rule["title"].strip()
            assert rule["statement"].strip()
            assert rule["explanation"].strip()
            assert len(rule["examples"]) >= 1
            for ex in rule["examples"]:
                assert ex["non_stf"].strip()
                assert ex["stf"].strip()
            all_rule_ids.append(rule["id"])

    assert len(all_rule_ids) == 53

    grs = data["general_recommendations"]
    assert [g["id"] for g in grs] == [f"GR-{i}" for i in range(1, 9)]
    for gr in grs:
        assert gr["title"].strip()
        assert gr["statement"].strip()
        assert gr["explanation"].strip()
        assert len(gr["examples"]) >= 1


def test_categories_json_completeness() -> None:
    """Verify categories.json covers all 22 noun categories and 4 verb categories."""
    data = _load_json("categories.json")
    noun_cats = data["technical_noun_categories"]
    verb_cats = data["technical_verb_categories"]

    assert [c["id"] for c in noun_cats] == list(range(1, 23))
    for cat in noun_cats:
        assert cat["title"].strip()
        assert cat["description"].strip()
        assert len(cat["examples"]) >= 3

    assert [c["id"] for c in verb_cats] == list(range(1, 5))
    for cat in verb_cats:
        assert cat["title"].strip()
        assert cat["description"].strip()
        assert len(cat["subcategories"]) >= 1
        for sub in cat["subcategories"]:
            assert sub["code"].strip()
            assert sub["title"].strip()
            assert len(sub["examples"]) >= 3


def test_dictionary_json_integrity_and_counts() -> None:
    """Verify dictionary.json counts, uniqueness, approved_ant coverage, and examples."""
    data = _load_json("dictionary.json")
    approved_ant = data["meta"]["approved_ant"]
    assert len(approved_ant) >= 20

    entries = data["entries"]
    keys = [(e["word"].lower(), e["pos"]) for e in entries]
    assert len(keys) == len(set(keys)), "Duplicate (word.lower(), pos) entries found"

    approved = [e for e in entries if e["approved"]]
    unapproved = [e for e in entries if not e["approved"]]
    approved_verbs = [e for e in approved if e["pos"] == "v"]

    assert len(approved) >= 450
    assert len(approved_verbs) >= 160
    assert len(unapproved) >= 150
    assert len(data["recurring_errors"]) >= 40

    approved_headwords = {e["word"].lower() for e in approved}
    unapproved_headwords = {e["word"].lower() for e in unapproved}
    assert approved_headwords.isdisjoint(unapproved_headwords)

    for ant in approved_ant:
        assert ant.lower() in approved_headwords

    for verb in approved_verbs:
        assert len(verb["forms"]) >= 1
        assert verb["meaning"].strip()
        assert verb["stf_example"].strip()

    for item in unapproved:
        assert len(item["alternatives"]) >= 1
        assert item["meaning"].strip()
        assert item["non_stf_example"].strip()
        assert item["stf_example"].strip()


def test_spec_examples_are_stf_compliant() -> None:
    """Verify all STF examples in rules.json and dictionary.json pass structural STF checks."""
    rules_data = _load_json("rules.json")
    dict_data = _load_json("dictionary.json")
    vocab = load_dictionary(SPEC_DIR / "dictionary.json")

    for sec in rules_data["sections"]:
        for rule in sec["rules"]:
            for ex in rule["examples"]:
                rep = Report()
                check_text(ex["stf"], "descriptive", rep, f"rule-{rule['id']}", vocab)
                assert not rep.errors, f"Rule {rule['id']} example failed: {rep.errors}"

    for entry in dict_data["entries"]:
        rep = Report()
        check_text(entry["stf_example"], "descriptive", rep, entry["word"], vocab)
        assert not rep.errors, f"Entry {entry['word']} example failed: {rep.errors}"


def test_sync_docs_check_and_drift_detection(tmp_path: Path) -> None:
    """Verify sync_docs.py --check passes on repo and fails if a generated file drifts."""
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync_docs.py"), "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res.returncode == 0, res.stderr + res.stdout

    # Verify JSON dictionary and generated Markdown dictionary load identically.
    json_vocab = load_dictionary(SPEC_DIR / "dictionary.json")
    md_vocab = load_dictionary(
        REPO_ROOT / "skills" / "francais-technique-simplifie" / "references" / "dictionnaire-stf.md"
    )
    assert json_vocab.approved == md_vocab.approved
    assert json_vocab.unapproved == md_vocab.unapproved
    assert json_vocab.approved_ant == md_vocab.approved_ant

    # Copy minimal tree into tmp_path and mutate one generated file to test --check failure.
    shutil.copytree(SPEC_DIR, tmp_path / "spec")
    shutil.copytree(REPO_ROOT / "src", tmp_path / "src")
    res_sync = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync_docs.py"), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res_sync.returncode == 0, res_sync.stderr

    target = tmp_path / "docs" / "03-reference" / "regles-redaction.md"
    target.write_text("out of sync\n", encoding="utf-8")
    res_drift = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "sync_docs.py"),
            "--check",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res_drift.returncode == 1
    assert "OUT OF SYNC" in res_drift.stderr

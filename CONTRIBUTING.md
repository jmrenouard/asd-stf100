# Contribuer à ASD-STF100 / Contributing Guide

Merci de contribuer au projet **ASD-STF100** (*Français Technique Simplifié*).
Respectez les règles d'ingénierie, de source unique et de séparation linguistique décrites ci-dessous.

---

## 1. Source unique de vérité (`spec/*.json`)

Les fichiers suivants sont **générés automatiquement** par `scripts/sync_docs.py` et ne doivent jamais être modifiés à la main :

- `docs/03-reference/regles-redaction.md`
- `docs/03-reference/dictionnaire-stf.md`
- `docs/03-reference/categories-techniques.md`
- `skills/francais-technique-simplifie/references/regles-redaction.md`
- `skills/francais-technique-simplifie/references/dictionnaire-stf.md`
- `skills/francais-technique-simplifie/references/substitutions.md`
- `skills/francais-technique-simplifie/scripts/stf_check.py`

Pour modifier une règle, une catégorie ou une entrée du dictionnaire :

1. Éditez `spec/rules.json`, `spec/categories.json` ou `spec/dictionary.json`.
2. Exécutez `python scripts/sync_docs.py`.
3. Vérifiez que `python scripts/sync_docs.py --check` retourne `0`.

Les scripts `skills/diataxis-docs-fr/scripts/{scaffold_diataxis_fr.py, diataxis_check_fr.py}` doivent rester strictement identiques à ceux de `src/asd_stf100/`.

---

## 2. Validations obligatoires avant toute Pull Request

Exécutez ces commandes et assurez-vous qu'elles retournent `0` :

```bash
pytest -v
python scripts/sync_docs.py --check
python -m asd_stf100.diataxis_check_fr docs --strict --check-stf
```

Si vous modifiez le générateur PDF ou `spec/*.json`, recompilez également la norme :

```bash
python scripts/build_pdf.py --output dist/ASD-STF100_ISSUE1.pdf
```

---

## 3. Politique linguistique stricte (English-Only GitHub & Code Comments)

1. **GitHub Issues, Pull Requests & Commits (STRICTLY ENGLISH):** All issue titles/bodies, PR titles/descriptions, review comments, and Conventional Commit messages (`feat:`, `fix:`, `docs:`, `chore:`, `test:`) MUST be written strictly in **English**.
2. **Source Code Comments & Docstrings (STRICTLY ENGLISH):** All comments and docstrings inside Python files (`src/`, `scripts/`, `tests/`) and workflow YAML comments MUST be written strictly in **English**.
3. **Specification, Documentation & Skills Prose (FRENCH):** Specification data (`spec/*.json`), `docs/`, French Agent Skills (`skills/`), and rendered PDF text are authored in **French**, respecting **ASD-STF100** strictly under `docs/02-guides-pratiques/`.

---

## 4. Hygiène juridique

- Ne copiez jamais textuellement de définitions, phrases d'aide ou exemples provenant d'une spécification tierce protégée (notamment `ASD-STE100`).
- Rédigez des formulations et exemples techniques 100 % originaux.
- Préservez l'avis de non-affiliation et les mentions de licences MIT / CC-BY-SA-4.0 dans [`NOTICE.md`](NOTICE.md).

---

## 5. Flux GitHub

1. Ouvrez une issue GitHub décrivant le besoin ou le correctif.
2. Créez une branche dédiée depuis `main` (`feat/issue-<id>-<slug>`, `fix/issue-<id>-<slug>`, `docs/issue-<id>-<slug>`).
3. Exécutez 100 % des tests et contrôles avant chaque commit.
4. Ouvrez une Pull Request ciblant `main` et référençant l'issue (`Closes #<id>`).

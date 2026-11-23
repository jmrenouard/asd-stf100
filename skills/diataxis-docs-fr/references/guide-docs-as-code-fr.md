# Guide de la chaîne Docs-as-Code (FR)

Ce guide décrit les quatre couches d'automatisation générées par `scaffold_diataxis_fr.py --with-ci` pour maintenir une documentation française fiable dans la durée.

---

## 1. Couche 1 : `diataxis_check_fr.py` (Structure, liens, gouvernance et STF)

Exécutez le validateur localement avant chaque commit et en CI :

```bash
python scripts/diataxis_check_fr.py docs --strict --check-stf
```

Le script contrôle quatre aspects :

1. **Squelette obligatoire :** présence de `docs/index.md` et des quatre répertoires `01-tutoriels/`, `02-guides-pratiques/`, `03-reference/`, `04-explications/` avec leur `index.md`.
2. **Liens relatifs internes :** résolution sur disque de chaque lien Markdown hors blocs de code et code en ligne (les URL externes `http(s)://`, `mailto:` et ancres pures `#section` sont ignorées).
3. **Heuristiques par quadrant (`--strict` transforme `WARN` en `ERROR`) :**
   - `02-guides-pratiques/` : présence de validation (`Vérification`/`Validation`) et de retour arrière (`Retour arrière`/`Restauration`) ; rejet des titres théoriques (`## Pourquoi`, `## Architecture`, `## Théorie`, `## Contexte`).
   - `03-reference/` : présence d'au moins un tableau Markdown ou une liste structurée ; rejet des formulations de tutoriel (`Dans ce tutoriel`, `Étape 1`, `Commençons`).
   - `04-explications/` : rejet des titres procéduraux (`## Étape 1`, `## Retour arrière`, `## Remédiation`, `## Prérequis`).
4. **Contrôle ASD-STF100 (`--check-stf`) :** localisation automatique de `stf_check.py` (module frère ou skill `francais-technique-simplifie`) et exécution avec `--mode procedural` sur tous les fichiers non-index de `02-guides-pratiques/`.

---

## 2. Couche 2 : Vale et règles françaises `STF100` (`.vale.ini`)

La configuration `.vale.ini` applique le style local `.vale/styles/STF100/` sans dépendance réseau externe :

- **`ModauxInterdits.yml` (`error`) :** bloque `devrait`, `devraient`, `pourrait`, `pourraient`, `serait`, `seraient`, `faudrait`, `éventuellement`, `potentiellement`, `susceptible de`.
- **`PointVirgule.yml` (`error`) :** interdit le point-virgule `;` hors blocs de code (Règle 8.1).
- **`LocutionsLourdes.yml` (`warning`) :** signale `afin de`, `en vue de`, `dans le but de`, `au niveau de`, `par le biais de`, `préalablement à`, `procéder à`, `effectuer un/une`, `à l'aide de`, `vous devez`, `il faut`, `il convient de`, `il est nécessaire de`.
- **`AbreviationsLatines.yml` (`warning`) :** signale `e.g.`, `i.e.`, `etc.`, `cf.` (`GR-6`).

Sur `docs/02-guides-pratiques/**/*.md`, les surcharges au niveau des règles (`STF100.AbreviationsLatines = error`, `STF100.LocutionsLourdes = error`, `STF100.ModauxInterdits = error`, `STF100.PointVirgule = error`) garantissent une conformité stricte dès l'édition dans l'IDE.

---

## 3. Couche 3 : `markdownlint` (`.markdownlint.json`)

La configuration JSON impose :

- Un titre de niveau 1 en début de document (`MD041`).
- Des blocs de code clôturés homogènes avec triple accent grave (`MD046: fenced`).
- La tolérance des titres identiques entre sections distinctes (`MD024: siblings_only`).
- Une longueur de ligne maximale de 120 caractères hors tableaux et blocs de code (`MD013`).

---

## 4. Couche 4 : MkDocs Material et GitHub Actions (`mkdocs.yml` & `docs-ci.yml`)

Le fichier `mkdocs.yml` configure MkDocs Material en français (`language: fr`) avec navigation par onglets, index cliquables, copie de code et coloration syntaxique.
Le workflow `.github/workflows/docs-ci.yml` exécute séquentiellement :

1. `diataxis_check_fr.py docs --strict --check-stf`
2. `markdownlint-cli2` sur `docs/**/*.md`
3. `vale` sur `docs/02-guides-pratiques`
4. `mkdocs build --strict`

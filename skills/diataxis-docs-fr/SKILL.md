---
name: diataxis-docs-fr
description: >
  Architecture documentaire Diátaxis (FR) et chaîne Docs-as-Code pour projets logiciels, bases de données, DevOps et infrastructure. À activer pour concevoir, initialiser, rédiger, refactoriser ou auditer une arborescence docs/ en français : 01-tutoriels/, 02-guides-pratiques/ (runbooks ASD-STF100), 03-reference/, 04-explications/ (ADR), MkDocs Material, Vale STF100, markdownlint et pipelines CI (French Diataxis documentation architecture and Docs-as-Code validation).
---

# Architecture documentaire Diátaxis (FR) et Docs-as-Code

Appliquez ce skill pour concevoir, initialiser, rédiger, réorganiser ou auditer une documentation technique francophone sous `docs/`.

---

## 1. La matrice à 2 axes et 4 quadrants

Diátaxis classe toute documentation selon deux axes orthogonaux :

- **Pratique vs Théorique :** agir sur le système ou comprendre son fonctionnement.
- **Acquisition vs Application :** apprendre en étudiant ou travailler en production.

| | **Pratique (Action)** | **Théorique (Cognition)** |
| :--- | :--- | :--- |
| **Acquisition (Apprendre)** | **1. Tutoriels (`01-tutoriels/`)**<br>Leçons guidées en environnement isolé | **4. Explications (`04-explications/`)**<br>Architecture, compromis et dossiers ADR |
| **Application (Travailler)** | **2. Guides pratiques (`02-guides-pratiques/`)**<br>Procédures et runbooks en ASD-STF100 | **3. Référence (`03-reference/`)**<br>Spécifications neutres, tableaux et CLI |

> **Règle d'or :** Ne mélangez jamais deux genres sur une même page. Gardez chaque fichier dans un seul quadrant et reliez les quadrants par liens relatifs plutôt que de dupliquer le contenu.

---

## 2. Arborescence canonique `docs/` (profil `infra`)

```text
docs/
├── index.md                                   # Portail documentaire et points d'entrée
├── assets/
│   ├── architecture/                          # Diagrammes statiques SVG/PNG
│   └── runbooks/                              # Captures et journaux d'exécution
├── 01-tutoriels/
│   └── index.md                               # Leçons guidées locales et reproductibles
├── 02-guides-pratiques/
│   ├── index.md
│   ├── deploiement/                           # Installation, migration, mise à niveau
│   ├── exploitation/                          # Maintenance courante et Day-2
│   ├── gestion-incidents/                     # Runbooks d'astreinte (ASD-STF100 strict)
│   └── securite/                              # Rotation de secrets, durcissement, audit
├── 03-reference/
│   ├── index.md
│   ├── architecture-specs/                    # Dimensionnement, SLA, flux réseau
│   ├── configuration/                         # Paramètres, types, valeurs par défaut, unités
│   ├── cli-et-scripts/                        # Options CLI, variables et codes retour
│   └── codes-erreurs/                         # Matrices d'alertes et renvois runbooks
└── 04-explications/
    ├── index.md
    ├── vue-architecture/                      # Topologie système et flux de données
    ├── decisions-architecture/                # Architecture Decision Records (ADR)
    └── analyses-internes/                     # Mécanismes internes et postmortems
```

---

## 3. Garde-fous par quadrant

| Quadrant | Ton et style | Éléments requis | Éléments interdits |
| :--- | :--- | :--- | :--- |
| **`01-tutoriels/`** | Pédagogique, guidé, sûr, reproductible. | Prérequis locaux isolés, étapes numérotées, commandes exactes, résultats attendus, liens « Prochaines étapes ». | Avertissements de production enfouis, options multiples non guidées, débats d'architecture. |
| **`02-guides-pratiques/`** | **ASD-STF100 strict** (`francais-technique-simplifie`, validé par `stf_check.py --mode procedural`). Impératif actif, `<= 20` mots/phrase. | Prérequis, consignes `AVERTISSEMENT`/`ATTENTION`, étapes à 1 action, `Vérification`, `Retour arrière`, liens `03-reference/` et `04-explications/`. | Voix passive avec `par`, point-virgule, `devrait/pourrait/serait/éventuellement`, gérondifs, titres théoriques (`## Pourquoi`, `## Architecture`, `## Théorie`, `## Contexte`). |
| **`03-reference/`** | Sec, neutre, exact, exhaustif. | Tableaux Markdown ou listes structurées (paramètres, flux, options CLI, codes retour, matrices d'alertes). | Style narratif, formules de tutoriel (`Dans ce tutoriel`, `Étape 1`, `Commençons`), opinions. |
| **`04-explications/`** | Analytique, contextuel, comparatif. | Contexte, contraintes, schémas Mermaid, tableau d'options et compromis, décision ADR, liens `03-reference/`. | Commandes pas à pas d'exécution, titres procéduraux (`## Étape 1`, `## Retour arrière`, `## Remédiation`, `## Prérequis`). |

---

## 4. Contrat de maillage inter-quadrants

1. **Runbook (`02-guides-pratiques/.../<runbook>.md`)**
   - En-tête : lien vers `../../03-reference/codes-erreurs/matrice-alertes.md`.
   - Pied de page : lien vers `../../04-explications/vue-architecture/<topologie>.md`.
2. **Dossier ADR (`04-explications/decisions-architecture/<adr>.md`)**
   - Pied de page : lien vers `../../03-reference/configuration/<parametres>.md` et, si besoin, vers le guide associé.
3. **Matrice d'alertes (`03-reference/codes-erreurs/matrice-alertes.md`)**
   - Colonne remédiation : lien relatif direct vers le runbook sous `../../02-guides-pratiques/gestion-incidents/`.
4. **Tutoriel (`01-tutoriels/<lecon>.md`)**
   - Section « Prochaines étapes » : liens vers `../02-guides-pratiques/index.md`, `../03-reference/index.md` et `../04-explications/index.md`.

---

## 5. Automatisation CLI (`scaffold_diataxis_fr.py` & `diataxis_check_fr.py`)

```bash
# Générer l'arborescence complète infra + chaîne Docs-as-Code
python scripts/scaffold_diataxis_fr.py <repertoire_cible> --profile infra --with-ci

# Générer un squelette logiciel minimal
python scripts/scaffold_diataxis_fr.py <repertoire_cible> --profile logiciel

# Prévisualiser sans modifier le disque
python scripts/scaffold_diataxis_fr.py <repertoire_cible> --profile infra --with-ci --dry-run

# Auditer structure, liens relatifs, gouvernance et conformité ASD-STF100
python scripts/diataxis_check_fr.py <repertoire_docs> --strict --check-stf
```

---

## 6. Ressources du skill

- Règles de classement, anti-patrons et compatibilité moteurs statiques : [regles-diataxis-fr.md](references/regles-diataxis-fr.md)
- Guide détaillé de la chaîne CI Docs-as-Code : [guide-docs-as-code-fr.md](references/guide-docs-as-code-fr.md)
- Modèles prêts à l'emploi :
  - [01-tutoriel.md](templates/01-tutoriel.md)
  - [02-guide-pratique-runbook.md](templates/02-guide-pratique-runbook.md)
  - [03-reference.md](templates/03-reference.md)
  - [04-explication-adr.md](templates/04-explication-adr.md)
  - Configurations sous `templates/docs-as-code/` (`mkdocs.yml`, `.vale.ini`, `.markdownlint.json`, `docs-ci.yml`, `vale-styles/STF100/*.yml`)

# Référence : Matrice Diátaxis (FR) et contrat de maillage

Spécification canonique de l'architecture documentaire **Diátaxis (FR)**
appliquée aux projets logiciels et d'infrastructure.

## 1. Matrice à 2 axes et 4 quadrants

| Quadrant | Répertoire canonique | Axe d'action / cognition | Moment d'utilisation | Ton et norme linguistique |
| :--- | :--- | :--- | :--- | :--- |
| **Tutoriels** | `01-tutoriels/` | Pratique / Acquisition | Apprentissage initial (bac à sable) | Pédagogique, guidé, sûr, reproductible |
| **Guides pratiques** | `02-guides-pratiques/` | Pratique / Application | Exploitation et astreinte | **ASD-STF100 strict** (`<= 20` mots/phrase, impératif actif) |
| **Référence** | `03-reference/` | Théorique / Application | Consultation rapide en travail | Factuel, neutre, exhaustif, tabulaire |
| **Explications** | `04-explications/` | Théorique / Acquisition | Étude d'architecture et revue | Analytique, conceptuel, comparatif |

## 2. Arborescence canonique (profil `infra`)

| Chemin relatif | Rôle | Exemples de documents |
| :--- | :--- | :--- |
| `docs/index.md` | Portail d'entrée | Tableau des 4 quadrants, liens principaux |
| `docs/assets/architecture/` | Diagrammes statiques | Schémas réseau SVG/PNG |
| `docs/assets/runbooks/` | Captures et preuves | Journaux terminaux d'intervention |
| `docs/01-tutoriels/` | Leçons guidées | `01-demarrage-rapide.md`, `02-lab-bascule.md` |
| `docs/02-guides-pratiques/deploiement/` | Installation et mise à niveau | Déploiement, migration de schéma |
| `docs/02-guides-pratiques/exploitation/` | Maintenance courante | Sauvegarde, purge, bascule planifiée |
| `docs/02-guides-pratiques/gestion-incidents/` | Runbooks d'astreinte | Reprise sur alerte critique |
| `docs/02-guides-pratiques/securite/` | Sécurité opérationnelle | Rotation de certificats, durcissement |
| `docs/03-reference/architecture-specs/` | Dimensionnement et SLA | Topologies de référence, débits |
| `docs/03-reference/configuration/` | Paramètres et valeurs | Variables d'environnement, fichiers YAML |
| `docs/03-reference/cli-et-scripts/` | Outils en ligne de commande | Options, variables, codes retour |
| `docs/03-reference/codes-erreurs/` | Matrices d'alertes | Codes d'erreur et renvois runbooks |
| `docs/04-explications/vue-architecture/` | Topologie et flux | Flux de données, modèles de sécurité |
| `docs/04-explications/decisions-architecture/` | Décisions (ADR) | `adr-001-...md`, matrice d'options |
| `docs/04-explications/analyses-internes/` | Études approfondies | Consensus, postmortems techniques |

## 3. Règles de validation automatisée (`diataxis_check_fr.py`)

| Quadrant | Contrôles obligatoires | Éléments signalés en avertissement (`--strict` -> erreur) |
| :--- | :--- | :--- |
| Structure globale | `docs/index.md` et `index.md` dans chaque quadrant | Répertoire ou `index.md` manquant (toujours `ERROR`) |
| Tous fichiers `.md` | Liens relatifs internes hors blocs de code | Cible introuvable sur disque (toujours `ERROR`) |
| `02-guides-pratiques/` | Sections/mots-clés de vérification (`Vérification`/`Validation`) et retour arrière (`Retour arrière`/`Restauration`) | Titre théorique (`## Pourquoi`, `## Architecture`, `## Théorie`, `## Contexte`) ou échec `stf_check.py --mode procedural` |
| `03-reference/` | Présence d'au moins un tableau Markdown ou d'une liste structurée | Formulations de tutoriel (`Dans ce tutoriel`, `Étape 1`, `Commençons`) |
| `04-explications/` | Prose analytique ou diagrammes | Titres procéduraux (`## Étape 1`, `## Retour arrière`, `## Remédiation`, `## Prérequis`) |

## 4. Contrat de maillage inter-quadrants

| Document source | Lien sortant requis | Cible canonique |
| :--- | :--- | :--- |
| Runbook (`02-guides-pratiques/`) | En-tête : seuils et paramètres | `../03-reference/...` |
| Runbook (`02-guides-pratiques/`) | Pied de page : contexte système | `../04-explications/...` |
| ADR (`04-explications/`) | Pied de page : paramètres exacts | `../03-reference/...` |
| Matrice d'erreurs (`03-reference/`) | Colonne remédiation : runbook dédié | `../02-guides-pratiques/...` |
| Tutoriel (`01-tutoriels/`) | Prochaines étapes : les 3 autres quadrants | `../02-guides-pratiques/index.md`, `../03-reference/index.md`, `../04-explications/index.md` |

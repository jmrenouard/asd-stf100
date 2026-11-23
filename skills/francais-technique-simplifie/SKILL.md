---
name: francais-technique-simplifie
description: Rédige, réécrit et audite des procédures opérationnelles, runbooks d'astreinte, modes opératoires et consignes de sécurité en Français Technique Simplifié (ASD-STF100 Édition 1). À activer pour la rédaction ou la revue de 02-guides-pratiques/, procédures, runbooks, consignes AVERTISSEMENT/ATTENTION, ou lorsque l'utilisateur demande ASD-STF100, STF, français technique simplifié, langage contrôlé ou stf_check.py (French procedural writing, simplified technical French, operational runbooks, safety instructions).
license: MIT pour le texte du skill, les modèles, les exemples et les scripts ; CC-BY-SA-4.0 pour les données de la spécification dans references/. Consultez LICENSE et NOTICE.md.
metadata:
  source-specification: ASD-STF100 Édition 1 (2026-11-23)
---

# Français Technique Simplifié (ASD-STF100)

Ce skill aligne les procédures et documents techniques français sur la norme ouverte **ASD-STF100** (*Français Technique Simplifié*, Édition 1).
ASD-STF100 comprend **53 règles** (Sections 1 à 9), **8 recommandations générales** (`GR-1` à `GR-8`), **22 catégories de noms techniques**, **4 catégories de verbes techniques** et un dictionnaire contrôlé.

Appliquez ces règles pour tout texte opérationnel destiné à l'exploitation, à la maintenance ou à l'astreinte.
Consultez `references/regles-redaction.md` pour l'ensemble des 53 règles, `references/dictionnaire-stf.md` pour le lexique approuvé et `references/substitutions.md` pour les remplacements recommandés.

## Périmètre et placement Diátaxis

Appliquez **ASD-STF100** en mode strict aux procédures, runbooks d'astreinte, modes opératoires et consignes de sécurité.
Associez ce skill à **Diátaxis (FR)** (`diataxis-docs-fr` ou `diataxis-docs`) pour classer chaque document dans le bon quadrant :

- `02-guides-pratiques/` : procédures orientées objectif soumises au mode procédural strict.
- `01-tutoriels/`, `03-reference/`, `04-explications/` : gardez-les séparés des étapes opérationnelles.

N'appliquez pas les contraintes lexicales STF aux éléments suivants :

- Blocs de code, commandes CLI, chemins de fichiers, variables et messages système cités.
- Identifiants officiels de produits, composants ou documents.
- Formules mathématiques LaTeX (`$...$`, `$$...$$`).

## Étape 1 : Classer le texte

Avant de rédiger, distinguez les deux registres :

- **Texte procédural :** donne une instruction directe. Exemple : « Arrêtez le service principal. »
- **Texte descriptif :** donne un fait technique. Exemple : « Le collecteur transmet les métriques toutes les 10 secondes. »

Ne mélangez jamais des étapes procédurales et de longues explications dans un même paragraphe.

## Étape 2 : Appliquer les règles de verbes

- Utilisez uniquement les temps simples et l'impératif direct en procédure (`Vérifiez`, `Exécutez`, `Ouvrez`, `Arrêtez`).
- Utilisez la voix active. Bannissez la voix passive avec l'agent `par` (par exemple : « le nœud est arrêté par l'opérateur »).
- Supprimez les modaux conditionnels et adverbes d'incertitude : `devrait`, `devraient`, `pourrait`, `pourraient`, `serait`, `seraient`, `faudrait`, `éventuellement`, `potentiellement`, `susceptible de`.
- Supprimez les formules redondantes en procédure : `vous devez`, `il faut`, `il convient de`, `il est nécessaire de`.
- Évitez le gérondif (`en ...ant`) et les formes en `-ant` hors mots approuvés (`pendant`, `suivant`, `composant`, `identifiant`, `voyant`, `durant`, `avant`).
- Remplacez les locutions verbales lourdes (`procéder à`, `effectuer une`, `afin de`, `à l'aide de`) par des verbes directs et prépositions simples (`pour`, `avec`).

## Étape 3 : Respecter les limites de phrases et de structure

- Limitez chaque phrase procédurale et chaque consigne de sécurité à **20 mots ou moins** (Règle 5.1).
- Limitez chaque phrase descriptive et chaque `NOTE` à **25 mots ou moins** (Règles 5.5 et 6.3).
- Limitez chaque paragraphe à **6 phrases maximum** (Règle 6.6).
- Exprimez **une seule action par phrase**, sauf actions simultanées (Règle 5.2).
- Placez la **condition avant la commande**, séparées par une virgule (Règle 5.4). Exemple : « Si le disque est plein, purgez les journaux anciens. »
- Utilisez une `NOTE` uniquement pour un fait neutre, jamais pour une action ou une consigne de sécurité (Règle 5.5).
- Limitez les noms composés à **trois termes** ou reliez-les par des prépositions (Règle 2.1).
- Supprimez tous les **points-virgules** (`;`) et découpez en deux phrases (Règle 8.1).
- Bannissez les abréviations latines : `e.g.`, `i.e.`, `etc.`, `cf.` (`GR-6`).
- Comptez chaque nombre suivi d'une unité (`10 °C`, `15 secondes`, `100 Mo`) et chaque mot composé à trait d'union (`sous-système`, `arrêtez-le`) comme **un seul mot** (Règles 8.6 et 8.7).

## Étape 4 : Respecter le vocabulaire contrôlé

- Utilisez en priorité les mots approuvés listés dans `references/dictionnaire-stf.md`.
- Employez un **seul terme technique constant** pour désigner un composant ou un concept dans tout le document (Règle 1.11).
- Classez vos termes spécialisés selon les 22 catégories de noms techniques et 4 catégories de verbes techniques dans `references/substitutions.md`.
- Remplacez les anglicismes non approuvés et les erreurs récurrentes grâce aux alternatives de `references/substitutions.md`.

## Étape 5 : Rédiger les consignes de sécurité

- Réalisez une analyse de risque avant de choisir le mot-clé (Règle 7.1).
- Utilisez **`AVERTISSEMENT`** (ou `DANGER`) lorsqu'un risque de **blessure ou de mort** existe, même s'il s'accompagne de dégâts matériels.
- Utilisez **`ATTENTION`** lorsqu'un risque concerne uniquement le **matériel, le système ou les données**.
- Commencez la consigne par une **commande directe ou une condition claire** (Règle 7.2).
- Énoncez le **risque exact** dans la phrase qui suit (Règle 7.3).
- Exemple : `**AVERTISSEMENT :** Coupez l'alimentation principale avant d'ouvrir l'armoire. La tension électrique cause des blessures graves ou la mort.`

## Étape 6 : Vérifier automatiquement avec `stf_check.py`

Exécutez le linter inclus avant toute validation ou fusion :

1. Analysez une procédure ou un runbook :
   `python scripts/stf_check.py --mode procedural <fichier.md>`
2. Analysez un texte descriptif :
   `python scripts/stf_check.py --mode descriptive <fichier.md>`
3. Analysez un document mixte :
   `python scripts/stf_check.py --mode mixed <fichier.md>`
4. Corrigez toutes les erreurs (`ERROR`) et examinez les avertissements (`WARNING`), puis relancez jusqu'à obtenir le code retour `0`.

Le script vérifie automatiquement la structure, la longueur des phrases et paragraphes, les points-virgules, les modaux interdits, la voix passive avec `par`, les gérondifs, les locutions lourdes, les abréviations latines et le lexique. La validation finale du sens exact des termes reste sous la responsabilité du rédacteur.

## Fichiers du skill

- `references/regles-redaction.md` — Catalogue complet des 53 règles et 8 recommandations `GR-1` à `GR-8`.
- `references/dictionnaire-stf.md` — Dictionnaire contrôlé STF-100 (entrées approuvées, formes, alternatives et exemples).
- `references/substitutions.md` — Substitutions fréquentes, erreurs récurrentes, 22 catégories de noms et 4 catégories de verbes techniques.
- `examples/avant-apres.md` — Exemples originaux avant/après en français technique simplifié.
- `templates/procedure-runbook-fr.md` — Modèle prêt à l'emploi de runbook conforme à `stf_check.py --mode procedural`.
- `scripts/stf_check.py` — Linter Python autonome sans dépendance externe.
- `NOTICE.md` et `LICENSE` — Licences MIT / CC-BY-SA-4.0 et mention explicite de non-affiliation ASD.

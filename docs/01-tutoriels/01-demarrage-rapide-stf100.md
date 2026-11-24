# Tutoriel : Démarrage rapide avec ASD-STF100

> **Objectif pédagogique :** Installer `asd-stf100` dans un environnement virtuel isolé,
> lancer `stf-check` sur une procédure non conforme puis obtenir zéro erreur.
>
> **Avertissement d'environnement :** Exécutez ces commandes uniquement dans un répertoire temporaire local.

## Prérequis

Vérifiez que votre poste dispose des éléments suivants :

- Python `3.10` ou supérieur
- `git` installé sur le poste
- Un terminal (`PowerShell` sous Windows ou `bash` sous Linux/macOS)

## Ce que vous allez réaliser

À la fin de ce tutoriel, vous aurez :

1. Créé un environnement virtuel Python isolé et installé `asd-stf100`.
2. Analysé une procédure volontairement non conforme avec `stf-check`.
3. Corrigé le texte selon **ASD-STF100** et vérifié le code retour `0`.

## Étape 1 : Installer le paquet en environnement isolé

Créez un répertoire d'essai, clonez le dépôt et installez le paquet en mode éditable :

```bash
mkdir -p ~/stf100-bac-a-sable && cd ~/stf100-bac-a-sable
git clone https://github.com/jmrenouard/asd-stf100.git
cd asd-stf100
python -m venv .venv
source .venv/bin/activate  # Sous Windows PowerShell : .\.venv\Scripts\Activate.ps1
pip install -e .
```

Résultat attendu :

```text
Successfully installed asd-stf100-1.0.0
```

## Étape 2 : Analyser un exemple non conforme

Créez un fichier temporaire `/tmp/procedure_test.md` contenant des écarts typiques
(modal interdit, point-virgule, phrase trop longue et voix passive avec agent) :

```markdown
# Procédure de test

Il conviendrait de redémarrer le serveur applicatif ; cette opération pourrait éventuellement corrompre la session utilisateur lorsque le service est arrêté par l'administrateur sans prévenir les utilisateurs connectés à l'avance.
```

Lancez le linter en mode procédural :

```bash
stf-check --mode procedural /tmp/procedure_test.md
```

Résultat attendu (le code retour vaut `1`) :

```text
ERROR   /tmp/procedure_test.md:L3 [rule 5.1/6.3] sentence has 29 words (max 20): "Il conviendrait de redémarrer le serveur applicatif ; cet..."
ERROR   /tmp/procedure_test.md:L3 [rule 8.1] semicolon found: "Il conviendrait de redémarrer le serveur applicatif ; cet...". Split into two sentences.
ERROR   /tmp/procedure_test.md:L3 [rule 3.2] forbidden conditional or uncertainty word "pourrait": use direct mood or explicit condition.
ERROR   /tmp/procedure_test.md:L3 [rule 3.2] forbidden conditional or uncertainty word "éventuellement": use direct mood or explicit condition.
ERROR   /tmp/procedure_test.md:L3 [rule 3.6] passive voice with agent "est arrêté par": make the agent the subject.
WARNING /tmp/procedure_test.md:L3 [rule 1.1] unapproved word "pourrait": use POUVOIR (PRÉSENT) (entry POURRAIT).
WARNING /tmp/procedure_test.md:L3 [rule 1.1] unapproved word "éventuellement": use SI NÉCESSAIRE, SUPPRIMER (entry ÉVENTUELLEMENT).
WARNING /tmp/procedure_test.md:L3 [rule 1.1] unapproved word "prévenir": use AVERTIR, EMPÊCHER (entry PRÉVENIR).

CHECK   5 words are not in the approved dictionary.
        Each must be an approved technical noun (22 categories) or technical verb (4 categories):
        conviendrait, applicatif, corrompre, session, administrateur

Result: 5 errors, 3 warnings.
```

## Étape 3 : Réécrire et valider en ASD-STF100

Remplacez le contenu de `/tmp/procedure_test.md` par une consigne directe et courte :

```markdown
# Procédure de test

**ATTENTION :** Déconnectez les sessions actives avant d'arrêter le serveur applicatif. Un arrêt brutal peut endommager les données utilisateur.

1. Informez les utilisateurs avant la maintenance.
2. Arrêtez le service applicatif.
3. Redémarrez le serveur cible.
```

Relancez le linter :

```bash
stf-check --mode procedural /tmp/procedure_test.md
```

Résultat attendu (le code retour vaut `0`) :

```text
Result: 0 errors, 0 warnings.
The text obeys the ASD-STF100 structural rules verified by this linter.
Manual review remains required to verify approved word meanings.
```

## Étape 4 : Nettoyer l'environnement d'essai

Désactivez l'environnement virtuel et supprimez les fichiers de test :

```bash
deactivate
rm -rf ~/stf100-bac-a-sable /tmp/procedure_test.md
```

## Prochaines étapes

- Rédiger un vrai guide opérationnel : [Guides pratiques](../02-guides-pratiques/index.md)
- Parcourir les 53 règles et le dictionnaire : [Référence](../03-reference/index.md)
- Comprendre les choix de conception : [Explications](../04-explications/index.md)

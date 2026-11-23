# Générer le PDF de spécification

Consultez les [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md)
pour la syntaxe exacte des scripts.

## Prérequis

- Installez les dépendances optionnelles PDF et test du projet :

  ```bash
  pip install -e ".[pdf,dev]"
  ```

- Vérifiez la présence des fichiers JSON dans `spec/`.

## Consignes de sécurité

**ATTENTION :** Exécutez toujours `sync_docs.py --check` avant de compiler le PDF final.
Des données désynchronisées créent un écart entre le PDF et le Markdown.

## Étapes

1. Vérifiez la synchronisation des données JSON et des fichiers générés :

   ```bash
   python scripts/sync_docs.py --check
   ```

2. Si une divergence apparaît, exécutez `python scripts/sync_docs.py`.
3. Lancez le script de génération du PDF vers `dist/` :

   ```bash
   python scripts/build_pdf.py --output dist/ASD-STF100_ISSUE1.pdf
   ```

4. Attendez la fin de la double passe ReportLab pour la table des matières.

## Vérification

1. Exécutez la suite de tests automatisés complète :

   ```bash
   pytest -v
   ```

2. Vérifiez que `dist/ASD-STF100_ISSUE1.pdf` existe et dépasse 100 Ko.
3. Confirmez que tous les tests d'intégrité PDF passent sans erreur.

## Retour arrière

1. Si le nouveau PDF présente un défaut visuel, restaurez la version précédente :

   ```bash
   git checkout -- dist/ASD-STF100_ISSUE1.pdf
   ```

2. Corrigez le script `scripts/build_pdf.py` avant une nouvelle compilation.

## Documentation associée

- Référence des commandes : [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md)
- Décision technique : [ADR-001 — Adaptation française](../04-explications/adr-001-adaptation-francaise.md)

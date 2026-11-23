# Rédiger une consigne de sécurité

Consultez les [Règles de rédaction](../03-reference/regles-redaction.md)
avant toute rédaction de sécurité.

## Prérequis

- Analysez les risques humains et matériels de l'intervention.
- Identifiez la cause exacte de chaque danger potentiel.
- Vérifiez que le document se trouve dans `02-guides-pratiques/`.

## Consignes de sécurité

**AVERTISSEMENT :** Évaluez le risque corporel avant de choisir le mot-clé de sécurité.
Une classification incorrecte expose les opérateurs à des blessures graves.

## Étapes

1. Listez tous les dangers liés à la tâche technique.
2. Si le danger cause une blessure ou la mort, sélectionnez `AVERTISSEMENT`.
3. Si le danger cause uniquement un dommage matériel ou logiciel, sélectionnez `ATTENTION`.
4. Si le danger combine un risque corporel et matériel, sélectionnez `AVERTISSEMENT`.
5. Placez la consigne immédiatement avant l'étape critique concernée.
6. Démarrez la consigne par une commande directe ou une condition claire.
7. Indiquez le risque exact dans la phrase qui suit la commande.
8. Limitez chaque phrase de la consigne à 20 mots ou moins.
9. N'utilisez jamais une simple note pour une règle de sécurité.

**NOTE :** Réservez la mention `NOTE` aux informations neutres sans aucun risque.

## Vérification

1. Vérifiez le fichier avec `stf-check` en mode procédural :

   ```bash
   python -m asd_stf100.stf_check --mode procedural docs/02-guides-pratiques/<fichier>.md
   ```

2. Vérifiez que chaque bloc `AVERTISSEMENT` ou `ATTENTION` indique la commande puis le risque.

## Retour arrière

1. Si une consigne bloque une étape par erreur, consultez le responsable sécurité du projet.
2. Corrigez la formulation puis validez à nouveau le fichier avec `stf-check`.

## Documentation associée

- Options du linter : [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md)
- Choix d'adaptation : [ADR-001 — Adaptation française](../04-explications/adr-001-adaptation-francaise.md)

# Règles de gouvernance Diátaxis (FR), arbre de décision et refactoring

Ce guide complète [SKILL.md](../SKILL.md) avec l'arbre de décision en quatre questions, des exemples de découpage d'anciens documents monolithiques et les règles de compatibilité des moteurs statiques.

---

## 1. Arbre de décision en 4 questions

Posez ces quatre questions dans l'ordre avant de créer ou déplacer un fichier Markdown :

```text
1. Le lecteur étudie-t-il en sécurité dans un bac à sable local avec résultats attendus ?
   ├── OUI -> 01-tutoriels/
   └── NON -> Question 2.

2. Le lecteur doit-il exécuter des étapes exactes pour un objectif réel ou un incident ?
   ├── OUI -> 02-guides-pratiques/  (Appliquer ASD-STF100 strict en mode procédural)
   └── NON -> Question 3.

3. Le lecteur cherche-t-il des faits secs (paramètres, défauts, ports, CLI, codes d'erreur) ?
   ├── OUI -> 03-reference/
   └── NON -> Question 4.

4. Le lecteur souhaite-t-il comprendre l'architecture, les compromis ou le pourquoi d'une décision ?
   └── OUI -> 04-explications/
```

### Tableau de placement rapide

| Type de contenu | Répertoire cible | Exigences clés |
| :--- | :--- | :--- |
| Atelier d'onboarding Docker/VM | `01-tutoriels/` | Bac à sable isolé et reproductible depuis zéro. |
| Runbook de remédiation d'astreinte | `02-guides-pratiques/gestion-incidents/` | Doit passer `stf_check.py --mode procedural`. |
| Rotation TLS ou mise à niveau | `02-guides-pratiques/securite/` ou `deploiement/` | Prérequis + étapes 1-action + vérification + retour arrière. |
| Variables d'environnement / schéma YAML | `03-reference/configuration/` | Type, valeur par défaut, unité et plage autorisée. |
| Catalogue d'alertes Prometheus | `03-reference/codes-erreurs/` | Chaque code d'alerte pointe directement vers un runbook. |
| Architecture Decision Record (ADR) | `04-explications/decisions-architecture/` | Contexte, tableau d'options, décision, conséquences. |
| Fonctionnement interne / consensus | `04-explications/analyses-internes/` | Prose conceptuelle et schémas Mermaid sans commandes d'exploitation. |

---

## 2. Exemples de refactoring d'anti-patrons

### Anti-patron : le guide monolithique « tout-en-un »

Mélanger théorie d'architecture, table de paramètres, bac à sable Docker et bascule de production dans un unique fichier de 400 lignes rend le document inutilisable lors d'un incident à 3 heures du matin.

### Solution : découper selon les 4 quadrants et relier

| Section du monolithe initial | Fichier cible | Action éditoriale |
| :--- | :--- | :--- |
| *« Comment lancer un cluster de test local »* | `docs/01-tutoriels/02-lab-bascule-ha.md` | Isoler uniquement le bac à sable Docker et ses sorties attendues. |
| *« Comment basculer le nœud primaire en production »* | `docs/02-guides-pratiques/gestion-incidents/bascule-primaire-manuelle.md` | Réécrire en ASD-STF100 (`<= 20` mots/phrase), ajouter `ATTENTION`, vérification et retour arrière. |
| *« Tableau TTL Patroni, loop_wait et port 8008 »* | `docs/03-reference/configuration/parametres-cluster.md` | Extraire en tableaux neutres avec types, défauts et unités. |
| *« Pourquoi choisir etcd plutôt que Keepalived »* | `docs/04-explications/decisions-architecture/adr-001-consensus.md` | Déplacer l'argumentaire, le schéma Mermaid et les compromis dans un ADR. |

### Anti-patron : explication théorique au milieu d'un runbook

**Avant (violation dans `02-guides-pratiques/`) :**

```markdown
## Pourquoi drainer les connexions
HAProxy maintient des connexions TCP persistantes et, si l'on ne coupe pas les écritures
avant de changer de leader, des anomalies de split-brain pourraient éventuellement survenir
car les transactions en vol n'ont pas été vidées vers la réplique synchrone.
```

**Après (conforme Diátaxis FR + ASD-STF100) :**

- Déplacez le paragraphe explicatif vers `docs/04-explications/vue-architecture/topologie.md`.
- Conservez uniquement la consigne de sécurité et l'action directe dans le runbook :

```markdown
**ATTENTION :** Arrêtez le trafic d'écriture client avant de lancer la bascule. Les écritures actives pendant la bascule endommagent les données.

1. Désactivez le trafic d'écriture sur le répartiteur applicatif.
```

---

## 3. Compatibilité entre moteurs de documentation statique

| Moteur | Comportement avec `01-tutoriels/` .. `04-explications/` |
| :--- | :--- |
| **MkDocs Material** | L'option `navigation.indexes` rend chaque `index.md` cliquable ; les préfixes numériques garantissent l'ordre de la barre latérale. |
| **Docusaurus** | Les dossiers numérotés ordonnent la navigation générée automatiquement ; les liens relatifs `.md` restent valides avec le versionnement et l'i18n. |
| **Antora** | Les quadrants s'intègrent dans `modules/ROOT/nav.adoc` et les schémas sous `assets/` restent séparés des pages `.md`. |

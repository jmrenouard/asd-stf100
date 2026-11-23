# Principes fondamentaux d'ASD-STF100

## Pourquoi une norme de français technique contrôlé

La documentation d'exploitation et de maintenance souffre souvent de phrases longues,
d'ambiguïtés modales et de synonymes inutiles.
En situation d'astreinte ou de maintenance critique, une phrase équivoque entraîne
une erreur d'exécution ou un délai d'analyse coûteux.

**ASD-STF100** (*Français Technique Simplifié*) transpose en français les principes d'un langage technique contrôlé :

- **Réduire la charge cognitive :** limiter la longueur des phrases (`<= 20` mots en procédure,
  `<= 25` mots en texte descriptif) et isoler une seule instruction par phrase.
- **Éliminer l'ambiguïté verbale :** privilégier l'impératif actif direct dans les étapes,
  supprimer la voix passive avec agent et bannir les modaux conditionnels
  (`devrait`, `pourrait`, `serait`, `éventuellement`).
- **Stabiliser la terminologie :** associer un seul mot ou nom technique français à chaque
  composant ou concept (`Règle 1.11`), afin d'éviter la dérive sémantique.

> **Rappel de non-affiliation :** `ASD-STF100` est une norme ouverte francophone indépendante.
> Elle s'inspire méthodologiquement d'`ASD-STE100` (Issue 9), marque déposée de l'ASD
> (UE n° `017966390`), sans reproduire ses définitions ni ses exemples officiels.

## Structure en 9 sections et 8 recommandations

L'architecture des **53 règles** suit neuf axes complémentaires :

1. **Vocabulaire et mots approuvés (`1.1` à `1.14`) :** séparation stricte entre lexique général
   contrôlé, 22 catégories de noms techniques et 4 catégories de verbes techniques.
2. **Noms composés (`2.1` à `2.2`) :** limitation à trois termes ou découpage explicite par
   préposition pour éviter l'empilement nominal.
3. **Verbes et voix (`3.1` à `3.7`) :** impératif direct en procédure, temps simples, rejet du
   passif avec `par`, rejet du gérondif en `-ant` hors liste approuvée et suppression des locutions lourdes.
4. **Structure de phrase (`4.1` à `4.5`) :** ordre logique, maintien des mots de liaison essentiels,
   listes verticales et présence d'articles ou démonstratifs.
5. **Rédaction procédurale (`5.1` à `5.5`) :** plafond de 20 mots, une instruction par phrase,
   condition avant la virgule et notes strictement informatives.
6. **Rédaction descriptive (`6.1` à `6.6`) :** plafond de 25 mots, six phrases par paragraphe,
   répétition assumée des termes clés et progression logique.
7. **Consignes de sécurité (`7.1` à `7.3`) :** analyse de risque distinguant `AVERTISSEMENT`
   (atteinte corporelle) et `ATTENTION` (dommage matériel ou perte de données), commande puis risque.
8. **Ponctuation et comptage (`8.1` à `8.7`) :** interdiction du point-virgule, parenthèses et
   nombres avec unité comptés comme un mot unique, gestion des traits d'union.
9. **Pratiques éditoriales (`9.1` à `9.4` + `GR-1` à `GR-8`) :** cohérence typographique,
   rejet des abréviations latines (`e.g.`, `etc.`, `cf.`), écriture neutre et clarté des pronoms.

## Ce que le linter automatise et ce qui reste humain

Un analyseur statique comme `stf_check.py` vérifie mécaniquement la longueur des phrases,
la taille des paragraphes, les points-virgules, les modaux interdits, la voix passive avec `par`,
les locutions lourdes et l'usage de termes non approuvés.

En revanche, seule une relecture humaine garantit que :

- Chaque mot approuvé conserve bien son sens technique exact dans le contexte.
- Une consigne de sécurité reflète une véritable analyse de risque (`AVERTISSEMENT` vs `ATTENTION`).
- L'ordre réel des opérations techniques est sûr et complet.

## Documentation associée

- Catalogue complet des 53 règles : [Règles de rédaction](../03-reference/regles-redaction.md)
- Dictionnaire et alternatives : [Dictionnaire contrôlé STF-100](../03-reference/dictionnaire-stf.md)
- Guide d'application : [Rédiger une procédure en ASD-STF100](../02-guides-pratiques/rediger-procedure-stf100.md)

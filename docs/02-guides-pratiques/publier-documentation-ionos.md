# Publier la documentation sur IONOS

Consultez les [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md)
pour la syntaxe des outils.

## Prérequis

- Disposez des droits administrateur sur le dépôt GitHub cible.
- Ouvrez le coffre KeePass avec les accès SFTP IONOS.
- Vérifiez l'accès au serveur distant IONOS par SFTP.
- Installez les dépendances de documentation dans votre environnement Python :

  ```bash
  pip install -e ".[dev]" -r requirements-docs.txt
  ```

## Consignes de sécurité

**ATTENTION :** Stockez les cinq secrets SFTP uniquement dans les secrets GitHub du dépôt.
Un secret écrit dans un fichier du dépôt expose le serveur distant.

## Étapes

1. Ouvrez les paramètres de sécurité du dépôt sur GitHub.
2. Ajoutez les cinq secrets SFTP IONOS :

   - `IONOS_FTP_SERVER` : nom d'hôte SFTP IONOS.
   - `IONOS_FTP_USERNAME` : identifiant du compte SFTP IONOS.
   - `IONOS_FTP_PASSWORD` : mot de passe du compte SFTP.
   - `IONOS_FTP_PORT` : numéro de port `22`.
   - `IONOS_REMOTE_PATH` : dossier distant `asd-stf100.lightpath.fr`.

3. Vérifiez que le dossier distant `asd-stf100.lightpath.fr` existe sur IONOS.
4. Vérifiez la synchronisation des fichiers générés depuis la source JSON :

   ```bash
   python scripts/sync_docs.py --check
   ```

5. Validez l'arborescence Diátaxis et les règles ASD-STF100 :

   ```bash
   python -m asd_stf100.diataxis_check_fr docs --strict --check-stf
   ```

6. Compilez la version `main` et les tags SemVer dans `site_dist/` :

   ```bash
   python scripts/build_versioned_docs.py --output site_dist --base-url https://asd-stf100.lightpath.fr --main-ref WORKTREE
   ```

7. Vérifiez la présence des six sorties critiques dans `site_dist/` :

   - `site_dist/versions.json`
   - `site_dist/index.html`
   - `site_dist/.htaccess`
   - `site_dist/main/index.html`
   - `site_dist/latest/index.html`
   - `site_dist/dev/index.html`

8. Poussez les modifications vers `main` ou publiez une release SemVer.
9. Suivez le flux de travail `.github/workflows/docs-publish.yml` sur GitHub Actions.

## Vérification

1. Vérifiez que le flux de travail de publication termine sans erreur.
2. Vérifiez que `site_dist/` exclut tout fichier `.kdbx`, `.keyx`, `.log` ou `.env*`.
3. Interrogez le manifeste et les routes sur `https://asd-stf100.lightpath.fr/` :

   ```bash
   curl -fsSL https://asd-stf100.lightpath.fr/versions.json
   curl -fsSLI https://asd-stf100.lightpath.fr/latest/
   curl -fsSLI https://asd-stf100.lightpath.fr/main/
   ```

4. Confirmez que `versions.json` liste chaque version publiée.
5. Confirmez le code HTTP `200` sur chaque URL cible.

**NOTE :** Si le DNS du sous-domaine reste inactif, la vérification HTTPS finale échoue.

## Retour arrière

1. Si une mise à jour casse le site publié, annulez le commit fautif :

   ```bash
   git revert <commit_fautif>
   git push origin main
   ```

2. Exécutez de nouveau `.github/workflows/docs-publish.yml` depuis une révision saine de `main`.
3. Si une release SemVer contient une erreur, publiez un nouveau tag correctif.

## Documentation associée

- Options des outils : [Commandes CLI et codes retour](../03-reference/cli-et-codes-retour.md)
- Choix d'architecture : [ADR-002 — Publication MkDocs versionnée sur IONOS](../04-explications/adr-002-publication-mkdocs-versionnee.md)

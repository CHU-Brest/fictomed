# Cartographie des dépendances

Page interactive servie via GitHub Pages : <https://chu-brest.github.io/fictomed/>

Elle visualise le graphe d'imports entre fichiers d'un dépôt sous forme de workflow type n8n (DAG, courbes Bézier, zoom/pan, drag, mini-map).

## Utilisation

1. Ouvre l'URL ci-dessus.
2. Le slug `CHU-Brest/fictomed` est pré-rempli, la branche par défaut est récupérée automatiquement via l'API.
3. Clique sur **Cartographier**.

## Changer de dépôt

Renseigne un autre `owner/repo` (GitHub ou GitLab), choisis le langage (Python, JS/TS, R, SQL) et le sens du flux, puis relance.

## Dépôt privé / quota API

Champ **PAT** : token GitHub avec scope `repo` (ou GitLab `read_repository`). Il est conservé uniquement en `sessionStorage` et perdu à la fermeture de l'onglet.

## Publication

Le dossier `docs/` est déployé automatiquement par `.github/workflows/pages.yml` à chaque push sur `prod`. À activer une fois dans **Settings → Pages → Source: GitHub Actions**.

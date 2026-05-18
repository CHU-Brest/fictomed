# fictomed

Librairie Python pour la génération de séjours médicaux fictifs et de scénarios textuels à partir de plusieurs stratégies spécifiques aux centres.

![Python](https://img.shields.io/badge/python-3.13+-blue)
[![CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-green.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Pipelines disponibles](#pipelines-disponibles)
- [Architecture](#architecture)
- [Cartographie](#cartographie)
- [Contribuer](#contribuer)
- [Licence](#licence)

---

## Vue d'ensemble

L'idée est de pouvoir crée des scénarios hospitaliers fictifs à partir de séjours choisi selon la stratégie mis en place par le centre développeur de la pipeline. Ces séjours fictifs peuvent ensuite être utilisés en entrée d'un LLM pour en générer des CRH par exemple.

---

## Installation

```bash
uv pip install fictomed
```

Ou depuis les sources :

```bash
git clone https://github.com/CHU-brest/fictomed.git
cd fictomed
pip install -e .
```

### Prérequis

- Python 3.13+
- polars
- pyyaml
- tqdm

---

## Utilisation

### En tant que librairie

```python
from fictomed import generate

df = generate(
    pipeline_name="brest",
    n_sejours=500,
    n_ccam=1,
    n_das=5,
    ghm5_pattern=None,
)
```

### En ligne de commande

```bash
python main.py brest --n-sejours 100
```

---

## Pipelines disponibles

| Nom | Site | Description |
|-----|------|-------------|
| `brest` | CHU de Brest | Choix des codes CIM10 par pondération selon les extractions SNDS |

---

## Architecture

```
fictomed/
├── __init__.py        # API publique
├── core.py            # Fonction principale generate()
├── registry.py        # Registre des pipelines (PIPELINES) ainsi que du chemin vers le fichier de config (CONFIG_DIR)
├── config.py          # Chargement de la configuration
├── base.py            # Définition de la pipeline de base BasePipeline
├── ficitve.py         # Fonction général qui permet la génération des séjours fictifs
├── scenario.py        # Fonction général qui permet la génération des scenarios fictifs
└── sites/
    └── brest/
        ├── __init__.py
        └── pipeline.py
```

---

## Cartographie

Visualisation interactive du graphe d'imports entre modules : <https://chu-brest.github.io/fictomed/>

Voir [docs/README.md](docs/README.md).

---

## Contribuer

### Ajouter un nouveau pipeline

1. Créer un dossier `fictomed/sites/<nom_site>/`
2. Implémenter `MedPipelineBase` dans `pipeline.py`
3. Enregistrer le pipeline dans `registry.py`

```python
# registry.py
from fictomed.sites.nouveau_site.pipeline import NouveauSitePipeline

PIPELINES = {
    "brest": BrestPipeline,
    "nouveau_site": NouveauSitePipeline,  # ← ajouter ici
}
```

## Contributeurs
 
| Nom | Rôle |
|-----|------|
| Arthur LAMARD | Data Engineer CHU Brest |
| Dr. Basile FUCHS | Médecin DIM CHU Brest |
| Claire Dechaux | Data Scientist INRIA |
| Dr. Remi Flicoteaux | Médecin DIM APHP |

## Licence
 
Ce projet est sous licence [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE.md).
 
 
Vous êtes libre de :
- **Partager** — copier et redistribuer le projet
- **Adapter** — remixer et transformer le projet
Sous les conditions suivantes :
- **Attribution** — Vous devez citer le projet original
- **Non Commercial** — Usage commercial interdit sans accord explicite
- **Partage dans les mêmes conditions** — Toute modification doit être publiée sous la même licence

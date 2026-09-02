# gallica-sdk

`gallica-sdk` est une bibliothèque Python légère pour accéder directement aux API publiques Gallica avec une interface cohérente, typée et testable.

Le projet ne crée pas une nouvelle API réseau. Il fournit une façade Python mince au-dessus des services Gallica pour les développeurs, notebooks, pipelines et outils automatisés.

## Statut

**0.1.0.dev0 — Phase 0 / vertical slice initial.**

Le périmètre initial volontairement réduit sert à valider l'architecture avant d'ajouter texte brut, PDF, périodiques, recherche dans OCR et outils de corpus.

## Installation de développement

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

Python 3.11+ est requis.

## Premier usage

```python
from gallica import Gallica

with Gallica() as g:
    doc = g.document("ark:/12148/bpt6k5738219s")

    print(doc.page_count())
    print(doc.metadata()[:200])

    page = doc.page(3)
    alto = page.alto()
    info = page.iiif_info()
    image = page.image(width=1000)
```

Recherche SRU :

```python
from gallica import Gallica

with Gallica() as g:
    xml = g.search('gallica all "Verdun"', maximum_records=10)
```

Le SRU et OAIRecord retournent encore volontairement leur XML brut dans ce vertical slice. Les modèles structurés ne seront ajoutés qu'après cartographie des formes de réponses réelles afin de ne pas figer trop tôt une abstraction incorrecte.

## Surface publique initiale

```text
Gallica.search()
Gallica.document()
Document.metadata()
Document.page_count()
Document.page()
Page.alto()
Page.iiif_info()
Page.image()
```

`Page.image()` utilise une largeur prudente de 1000 px par défaut. Les requêtes de largeur supérieure à 1000 px sont classées dans le bucket haute définition et limitées par le transport.

## Tests

Tests unitaires et d'intégration simulée :

```bash
pytest -m 'not live'
```

Validation contre les API publiques Gallica :

```bash
pytest -m live tests/test_live.py
```

La CI exécute les tests locaux sous Python 3.11 et 3.12 et un smoke test séparé depuis un runner GitHub public.

Une primitive réseau n'est considérée supportée que si sa requête, son comportement simulé et un scénario live pertinent sont couverts.

## Architecture et périmètre

- [`docs/architecture.md`](docs/architecture.md) : mission, principes, non-objectifs et architecture initiale.
- [`docs/capabilities.md`](docs/capabilities.md) : matrice des API Gallica connues, contraintes et ordre d'intégration.

Le dépôt `maribakulj/maj-scripts-api.bnf.fr` sert de source d'apprentissage sur les wrappers historiques et leurs défauts. `gallica-sdk` n'en dépend pas et ne reprend pas son architecture legacy.

## Pas encore dans la 0.1

- `.texteBrut` ;
- PDF ;
- Issues / périodiques ;
- ContentSearch ;
- outils de corpus ;
- DataFrame / Parquet ;
- CLI ;
- MCP ;
- async.

Ces fonctionnalités seront ajoutées par tranches verticales après validation des primitives déjà présentes.

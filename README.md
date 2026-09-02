# gallica-sdk

`gallica-sdk` est une bibliothèque Python légère pour accéder directement aux API publiques Gallica avec une interface cohérente, typée et testable.

Le projet ne crée pas une nouvelle API réseau. Il fournit une façade Python mince au-dessus des services Gallica pour les développeurs, notebooks, pipelines et outils automatisés.

## Statut

**0.1.0.dev0 — Phase 2 / résultats structurés.**

Le SDK couvre recherche SRU, métadonnées OAIRecord, pagination, OCR ALTO et texte brut, IIIF, recherche dans OCR et résolution de numéros de périodiques. SRU, OAIRecord et ContentSearch sont désormais transformés en objets Python typés tout en conservant le XML original dans `raw_xml`.

## Installation de développement

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

Python 3.11+ est requis.

## Recherche SRU

```python
from gallica import Gallica

with Gallica() as g:
    results = g.search('gallica all "Verdun"', maximum_records=10)

    print(results.total)
    for record in results:
        print(record.ark, record.title)
        print(record.values("creator"))

    raw_xml = results.raw_xml
```

Les champs Dublin Core sont répétables. `DublinCoreRecord.values("creator")` renvoie donc toujours un tuple plutôt que d'écraser silencieusement plusieurs auteurs.

## Document et métadonnées

```python
from gallica import Gallica

with Gallica() as g:
    doc = g.document("ark:/12148/bpt6k5738219s")
    metadata = doc.metadata()

    print(metadata.record.title)
    print(metadata.record.identifiers)
    print(metadata.indexing_mode)
    print(metadata.ocr_quality)
    print(doc.page_count())
```

`metadata.raw_xml` reste disponible pour les informations Gallica qui ne sont pas encore promues dans le modèle stable.

## OCR, recherche plein texte et IIIF

```python
from gallica import Gallica

with Gallica() as g:
    doc = g.document("bpt6k5460422k")

    text = doc.text()
    page_text = doc.page(1).text()

    matches = doc.search_text("hugo", start_result=1)
    for item in matches:
        print(item.page_id, item.content_html)

    page = doc.page(3)
    alto = page.alto()
    info = page.iiif_info()
    image = page.image(width=1000)
```

`ContentSearchResults` expose `total`, `query`, `items` et `raw_xml`. Le contenu des extraits reste du HTML fourni par Gallica dans `content_html`, il n'est pas transformé implicitement.

## Périodiques

```python
from datetime import date
from gallica import Gallica

with Gallica() as g:
    issue = g.periodical("cb32798952c").issue(date(1937, 3, 25))
    if issue is not None:
        print(issue.ark)
```

## Surface publique actuelle

```text
Gallica.search() -> SearchResults
Gallica.document() -> Document
Gallica.periodical() -> Periodical
Document.metadata() -> DocumentMetadata
Document.page_count() -> int
Document.text() -> str
Document.search_text() -> ContentSearchResults
Document.page() -> Page
Page.text() -> str
Page.alto() -> bytes
Page.iiif_info() -> dict
Page.image() -> bytes
Periodical.issue() -> Document | None
```

Modèles publics : `DublinCoreRecord`, `SearchResults`, `DocumentMetadata`, `ContentSearchItem`, `ContentSearchResults`.

`Page.image()` utilise une largeur prudente de 1000 px par défaut. Les requêtes de largeur supérieure à 1000 px sont classées dans le bucket haute définition et limitées par le transport. Les appels `.texteBrut` utilisent un bucket de 12,5 secondes afin de rester sous le quota public documenté de 5/minute.

### Pourquoi le PDF n'est pas encore exposé

Les deux formes historiques testées le 2 septembre 2026, `f1n1.pdf` puis `f1.pdf`, ont répondu HTTP 200 avec du HTML depuis un runner GitHub public au lieu d'un flux PDF. Le SDK ne fournit donc pas de méthode `pdf()` tant qu'un contrat public automatisable n'est pas caractérisé de manière reproductible.

## Tests

```bash
pytest -m 'not live'
pytest -m live tests/test_live.py
```

La CI exécute Ruff, mypy strict et les tests sous Python 3.11 et 3.12, puis un smoke test séparé depuis un runner GitHub public. Une primitive réseau n'est considérée supportée que si sa requête, son comportement simulé et un scénario live pertinent sont couverts.

## Architecture et périmètre

- [`docs/architecture.md`](docs/architecture.md) : mission, principes et non-objectifs.
- [`docs/capabilities.md`](docs/capabilities.md) : matrice des services Gallica, contraintes et statut d'intégration.

Le dépôt `maribakulj/maj-scripts-api.bnf.fr` sert de source d'apprentissage sur les wrappers historiques et leurs défauts. `gallica-sdk` n'en dépend pas et ne reprend pas son architecture legacy.

## Pas encore dans la 0.1

- accès PDF automatisé ;
- outils de corpus et reprise ;
- exports DataFrame / JSONL / Parquet ;
- CLI ;
- MCP ;
- async.

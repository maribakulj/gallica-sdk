# gallica-sdk

`gallica-sdk` est une bibliothèque Python légère pour accéder directement aux API publiques Gallica avec une interface cohérente, typée et testable.

Le projet ne crée pas une nouvelle API réseau. Il fournit une façade Python mince au-dessus des services Gallica pour les développeurs, notebooks, pipelines et outils automatisés.

## Statut

**0.2.0.dev0 — corpus reprenable avec artefacts documentaires et page par page.**

Le SDK couvre recherche SRU, métadonnées OAIRecord, pagination, OCR ALTO et texte brut, IIIF, recherche dans OCR, résolution de numéros de périodiques et traitement de corpus reprenable. SRU, OAIRecord et ContentSearch sont transformés en objets Python typés tout en conservant le XML original dans `raw_xml`.

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
```

Les champs Dublin Core sont répétables. Le XML source reste disponible dans `results.raw_xml`.

## Document

```python
from gallica import Gallica

with Gallica() as g:
    doc = g.document("ark:/12148/bpt6k5738219s")
    metadata = doc.metadata()

    print(metadata.record.title)
    print(metadata.indexing_mode)
    print(metadata.ocr_quality)
    print(doc.page_count())

    text = doc.text()
    matches = doc.search_text("hugo")

    page = doc.page(3)
    alto = page.alto()
    info = page.iiif_info()
    image = page.image(width=1000)
```

`DocumentMetadata`, `SearchResults` et `ContentSearchResults` conservent leur réponse XML originale dans `raw_xml`.

## Périodiques

```python
from datetime import date
from gallica import Gallica

with Gallica() as g:
    issue = g.periodical("cb32798952c").issue(date(1937, 3, 25))
    if issue is not None:
        print(issue.ark)
```

## Corpus reprenable

Métadonnées et texte :

```python
from gallica import Gallica

with Gallica() as g:
    report = g.corpus(["bpt6k5738219s", "bpt6k5460422k"]).fetch(
        "./corpus",
        metadata=True,
        text=True,
        resume=True,
    )
```

ALTO et images sur des vues explicites :

```python
with Gallica() as g:
    report = g.corpus(["bpt6k5619759j"]).fetch(
        "./corpus",
        metadata=False,
        alto=True,
        images=True,
        views=[1, 2, 3],
        image_width=1000,
        resume=True,
    )
```

Disposition :

```text
corpus/
├── manifest.jsonl
└── documents/
    └── <ark>/
        ├── metadata.json
        ├── text.txt
        └── pages/
            └── 1/
                ├── alto.xml
                └── image.jpg
```

Les écritures sont atomiques. La reprise vérifie chaque artefact demandé et ne récupère que ce qui manque. Une erreur sur un ARK est enregistrée sans interrompre les suivants. Les ARK et les vues sont dédupliqués en conservant leur ordre.

`alto=True` ou `images=True` exige `views=[...]`. Le SDK ne traduit jamais implicitement cette demande en « toutes les pages », afin d'éviter un téléchargement massif accidentel.

Référence complète : [`docs/corpus.md`](docs/corpus.md).

## Surface publique actuelle

```text
Gallica.search() -> SearchResults
Gallica.document() -> Document
Gallica.periodical() -> Periodical
Gallica.corpus() -> Corpus
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
Corpus.fetch() -> CorpusReport
```

Modèles publics : `DublinCoreRecord`, `SearchResults`, `DocumentMetadata`, `ContentSearchItem`, `ContentSearchResults`, `Corpus`, `CorpusItemResult`, `CorpusReport`.

`Page.image()` utilise 1000 px par défaut. Les largeurs supérieures à 1000 px passent par le bucket haute définition. `.texteBrut` utilise un bucket de 12,5 secondes afin de rester sous le quota public documenté de 5/minute.

### PDF

Les formes historiques `f1n1.pdf` et `f1.pdf` testées le 2 septembre 2026 ont répondu HTTP 200 avec du HTML depuis un runner GitHub public au lieu d'un flux PDF. Le SDK ne fournit donc pas de méthode `pdf()` tant qu'un contrat automatisable n'est pas caractérisé de manière reproductible.

## Tests

```bash
pytest -m 'not live'
pytest -m live tests/test_live.py
```

La CI exécute Ruff, mypy strict et les tests sous Python 3.11 et 3.12, puis un smoke test séparé depuis un runner GitHub public.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) : mission, principes et non-objectifs ;
- [`docs/capabilities.md`](docs/capabilities.md) : matrice des services et statut d'intégration ;
- [`docs/corpus.md`](docs/corpus.md) : contrat détaillé de corpus, reprise, manifest et erreurs.

Le dépôt `maribakulj/maj-scripts-api.bnf.fr` sert de source d'apprentissage sur les wrappers historiques et leurs défauts. `gallica-sdk` n'en dépend pas et ne reprend pas son architecture legacy.

## Pas encore dans la 0.2

- accès PDF automatisé ;
- sélection implicite de toutes les vues ;
- exports DataFrame / Parquet ;
- parallélisme / async ;
- CLI ;
- MCP.

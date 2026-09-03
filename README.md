# gallica-sdk

`gallica-sdk` est une couche de référence programmable et vérifiée pour accéder aux services publics Gallica.

Le projet fournit deux choses liées mais distinctes :

1. un SDK Python léger pour notebooks, scripts et pipelines ;
2. une représentation machine-readable des capacités, contraintes et services Gallica afin qu'un agent puisse raisonner sur une base validée plutôt que reconstruire l'API à chaque session.

Le projet ne crée pas une nouvelle API réseau et ne remplace pas la documentation BnF. Les services publics et la documentation BnF restent l'autorité ; `gallica-sdk` fournit une connaissance opérationnelle testée de leur utilisation.

## Statut

**0.2.0.dev0 — corpus reprenable, recherche paginée, packaging vérifié et référence programmable.**

Le SDK couvre recherche SRU, métadonnées OAIRecord, pagination, OCR ALTO et texte brut, IIIF, recherche dans OCR, résolution de numéros de périodiques et traitement de corpus reprenable. SRU, OAIRecord et ContentSearch sont transformés en objets Python typés tout en conservant le XML original dans `raw_xml`.

## Référence programmable

Un agent n'a pas besoin d'installer le package pour découvrir le périmètre validé du projet. Le dépôt publie :

```text
reference/
├── gallica-reference.json
└── schema.json
```

`reference/gallica-reference.json` fournit :

- les services Gallica actuellement connus du projet ;
- leur statut (`live-validated` ou `not-supported`) ;
- leurs URLs de base et sources documentaires ;
- les contraintes opérationnelles importantes ;
- un index de toutes les capacités publiques du SDK ;
- les invariants de validation du projet.

Le manifeste est versionné (`schema_version: 1.0`) et vérifié par CI contre la représentation Python canonique. Il peut être régénéré avec :

```bash
python scripts/export_reference.py
```

Les signatures détaillées restent disponibles via :

```bash
python scripts/export_capabilities.py
```

ou directement :

```python
from gallica import capabilities, programmable_reference

print(programmable_reference())
print(capabilities())
```

Cette séparation est volontaire : la référence de découverte reste petite et stable, tandis que le contrat détaillé expose paramètres, types, valeurs par défaut et contraintes de chaque opération.

## Installation de développement

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

Python 3.11+ est requis.

## Recherche SRU

Une page inspectable :

```python
from gallica import Gallica

with Gallica() as g:
    results = g.search('gallica all "Verdun"', maximum_records=10)

    print(results.total)
    print(results.arks)
    for record in results:
        print(record.ark, record.title)
        print(record.values("creator"))
```

Les champs Dublin Core sont répétables. Le XML source reste disponible dans `results.raw_xml`.

Pour parcourir plusieurs pages sans manipuler `startRecord` :

```python
with Gallica() as g:
    for record in g.search_all('gallica all "Verdun"', limit=200, page_size=50):
        print(record.ark, record.title)
```

`search_all()` est paresseux : les pages SRU sont demandées au fur et à mesure de l'itération. `page_size` reste limité à 50.

Export JSONL d'une page de résultats :

```python
with Gallica() as g:
    results = g.search('gallica all "Verdun"', maximum_records=50)
    results.write_jsonl("./verdun.jsonl")
```

Chaque ligne conserve tous les champs Dublin Core sous forme de listes et ajoute l'ARK normalisé lorsqu'il est identifiable.

## Recherche vers corpus

```python
with Gallica() as g:
    results = g.search('gallica all "Verdun"', maximum_records=20)
    report = g.corpus(results.arks).fetch(
        "./corpus",
        metadata=True,
        text=False,
        resume=True,
    )
```

Un exemple exécutable est fourni dans [`examples/search_to_corpus.py`](examples/search_to_corpus.py).

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

Les écritures sont atomiques. La reprise vérifie chaque artefact demandé et ne récupère que ce qui manque. Une erreur sur un ARK est enregistrée sans interrompre les suivants. Les ARK et les vues sont dédupliqués en conservant leur ordre.

`alto=True` ou `images=True` exige `views=[...]`. Le SDK ne traduit jamais implicitement cette demande en « toutes les pages ».

Référence complète : [`docs/corpus.md`](docs/corpus.md).

## Agents et génération de scripts

Le SDK ne contient pas de LLM et ne génère pas lui-même de code. Un agent peut d'abord lire `reference/gallica-reference.json`, puis utiliser le contrat détaillé pour écrire le script adapté.

```python
from gallica import Gallica

for capability in Gallica.capabilities():
    print(capability["id"], capability["call"], capability["constraints"])
```

`agent/recipes.json` fournit des compositions courantes qui référencent les mêmes identifiants de capacités, et les tests empêchent recettes, contrats et référence publiée de dériver silencieusement de l'API Python réelle.

Pour les agents de développement, le dépôt fournit [`AGENTS.md`](AGENTS.md). La référence détaillée est dans [`docs/agents.md`](docs/agents.md).

Cette couche n'est pas un MCP. Un MCP éventuel pourra être ajouté plus tard uniquement si un cas d'usage justifie réellement ce protocole supplémentaire.

## Surface publique actuelle

```text
programmable_reference() -> ReferenceSpec
capabilities() -> tuple[CapabilitySpec, ...]
Gallica.capabilities() -> tuple[CapabilitySpec, ...]
Gallica.search() -> SearchResults
Gallica.search_all() -> Iterator[DublinCoreRecord]
Gallica.document() -> Document
Gallica.periodical() -> Periodical
Gallica.corpus() -> Corpus
SearchResults.arks -> tuple[str, ...]
SearchResults.write_jsonl() -> Path
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

`Page.image()` utilise 1000 px par défaut. Les largeurs supérieures à 1000 px passent par le bucket haute définition. `.texteBrut` utilise un bucket de 12,5 secondes afin de rester sous le quota public documenté de 5/minute.

### PDF

Les formes historiques `f1n1.pdf` et `f1.pdf` testées le 2 septembre 2026 ont répondu HTTP 200 avec du HTML depuis un runner GitHub public au lieu d'un flux PDF. Le SDK ne fournit donc pas de méthode `pdf()` tant qu'un contrat automatisable n'est pas caractérisé de manière reproductible.

## Tests et packaging

```bash
pytest -m 'not live'
pytest -m live tests/test_live.py tests/test_live_usability.py
```

La CI exécute Ruff, mypy strict et les tests sous Python 3.11 et 3.12, puis un smoke test séparé depuis un runner GitHub public. Elle construit aussi le `sdist` et le wheel, réinstalle le wheel produit et vérifie que le package importé expose encore ses contrats.

## Documentation

- [`reference/gallica-reference.json`](reference/gallica-reference.json) : manifeste de découverte machine-readable ;
- [`reference/schema.json`](reference/schema.json) : schéma JSON de la référence ;
- [`docs/architecture.md`](docs/architecture.md) : mission, principes et non-objectifs ;
- [`docs/capabilities.md`](docs/capabilities.md) : matrice des services et statut d'intégration ;
- [`docs/corpus.md`](docs/corpus.md) : contrat détaillé de corpus, reprise, manifest et erreurs ;
- [`docs/agents.md`](docs/agents.md) : découverte machine-readable, recettes et règles pour agents ;
- [`AGENTS.md`](AGENTS.md) : instructions de développement pour agents travaillant sur le dépôt.

Le dépôt `maribakulj/maj-scripts-api.bnf.fr` sert de source d'apprentissage sur les wrappers historiques et leurs défauts. `gallica-sdk` n'en dépend pas et ne reprend pas son architecture legacy.

## Pas encore dans la 0.2

- accès PDF automatisé ;
- sélection implicite de toutes les vues ;
- export Parquet / DataFrame intégré ;
- parallélisme / async ;
- CLI ;
- MCP.

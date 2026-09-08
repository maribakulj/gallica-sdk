# gallica-sdk

`gallica-sdk` est une couche de référence programmable et vérifiée pour les services publics Gallica.

Le dépôt fournit deux choses liées :

1. un SDK Python léger pour notebooks, scripts et pipelines ;
2. une référence machine-readable des capacités, contraintes, services et preuves afin qu'un humain ou un agent puisse raisonner sur un contrat explicite plutôt que reconstruire l'API à chaque usage.

Le projet ne remplace ni les services Gallica ni la documentation BnF, qui restent l'autorité externe. Il formalise ce qui a été implémenté, testé et observé publiquement.

## Statut

**0.2.0.dev0 — version de développement.** Aucune release stable n'est encore publiée.

Le dépôt couvre aujourd'hui SRU, Categories, OAIRecord, Pagination, Toc, Issues, ContentSearch, OCR texte, ALTO, IIIF Image, IIIF Presentation et les compositions `Document`, `Page`, `Periodical` et `Corpus`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e .
```

Python 3.11+ est requis. Guide détaillé : [`docs/getting-started.md`](docs/getting-started.md).

## Démarrage rapide

```python
from gallica import Gallica

with Gallica() as gallica:
    document = gallica.document("ark:/12148/bpt6k5738219s")
    metadata = document.metadata()
    pagination = document.pagination()

    print(metadata.record.title)
    print(pagination.image_views)
```

Les ARK peuvent être fournis sous forme d'identifiant nu, d'`ark:/12148/...` ou d'URL Gallica canonique.

## Recherche SRU et Categories

```python
from gallica import Gallica

with Gallica() as gallica:
    results = gallica.search('gallica all "Verdun"', maximum_records=10)
    for record in results:
        print(record.ark, record.title)

    categories = gallica.categories('gallica all "Verdun"')
    for value in categories.for_category("language"):
        print(value.clean_value, value.approximate_count, value.cql_field)
```

Pour parcourir plusieurs pages SRU sans manipuler `startRecord` :

```python
with Gallica() as gallica:
    for record in gallica.search_all('gallica all "Verdun"', limit=200, page_size=50):
        print(record.ark, record.title)
```

Les champs Dublin Core restent répétables, le XML source SRU est conservé, et Categories expose explicitement des comptes `howMany` approximatifs. Le service Categories peut être `environment-limited` depuis certains runners publics ; le SDK rejette alors les réponses HTML/403 au lieu de les interpréter comme du JSON valide.

Guide : [`docs/search.md`](docs/search.md).

## Documents et pages

```python
with Gallica() as gallica:
    document = gallica.document("bpt6k5460422k")

    metadata = document.metadata()
    pagination = document.pagination()
    page_count = document.page_count()
    toc = document.toc()
    manifest = document.iiif_manifest()

    text = document.text()
    matches = document.search_text("hugo")
    geometry = document.search_text("hugo", page=173)

    page = document.page(3)
    page_text = page.text()
    alto = page.alto()
    info = page.iiif_info()
    image = page.image(width=1000)
```

`Pagination` conserve la structure de navigation et les labels logiques par vue. `TocDocument` préserve la différence entre anciens sommaires HTML et réponses TEI XML. `IIIFPresentationManifest` détecte explicitement Presentation v2 ou v3, conserve le JSON source et ne transforme pas artificiellement un manifeste v2 en v3. `IIIFImageInfo` expose dimensions et marqueurs de protocole sans inventer de version lorsqu'`info.json` ne s'auto-identifie pas. `ContentSearch` conserve les extraits, les dimensions master et toutes les boîtes OCR retournées pour une vue.

Guide : [`docs/documents.md`](docs/documents.md).

## Périodiques

```python
from datetime import date
from gallica import Gallica

with Gallica() as gallica:
    issue = gallica.periodical("cb32798952c").issue(date(1937, 3, 25))
    if issue is not None:
        print(issue.ark)
```

Guide : [`docs/periodicals.md`](docs/periodicals.md).

## Corpus reprenable

```python
from gallica import Gallica

with Gallica() as gallica:
    report = gallica.corpus(["bpt6k5738219s", "bpt6k5460422k"]).fetch(
        "./corpus",
        metadata=True,
        text=True,
        resume=True,
    )
```

ALTO et images exigent des vues explicites :

```python
with Gallica() as gallica:
    report = gallica.corpus(["bpt6k5619759j"]).fetch(
        "./corpus",
        metadata=False,
        alto=True,
        images=True,
        views=[1, 2, 3],
        image_width=1000,
        resume=True,
    )
```

Les écritures sont atomiques. La reprise vérifie fingerprint de requête, taille et SHA-256. Les erreurs ordinaires sont isolées par artefact, de sorte qu'un échec n'empêche pas les artefacts ou ARK indépendants de continuer. Le manifest conserve paramètres, version SDK, checksums et provenance d'échec.

Guide : [`docs/corpus.md`](docs/corpus.md).

## CLI

Le package installe une CLI volontairement mince et JSON-first :

```bash
gallica capabilities
gallica contract page_alto
gallica search 'gallica all "Verdun"' --limit 5
gallica categories 'gallica all "Verdun"'
gallica metadata bpt6k5738219s
gallica page-count bpt6k5738219s
gallica pagination bpt6k5738219s
gallica toc bpt6k97540464
gallica iiif-manifest btv1b550076223
gallica iiif-info btv1b53066668g 1
```

Elle réutilise exclusivement les primitives du SDK au lieu de maintenir une deuxième logique réseau. Guide : [`docs/cli.md`](docs/cli.md).

## Référence programmable

Le dépôt contient une représentation machine-readable du contrat :

```text
reference/
├── gallica-reference.json
└── schema.json
```

Le manifeste checked-in est actuellement en `schema_version: 2.0`.

`programmable_reference()` relie capacités, services, statuts, preuves et invariants. `capabilities()` décrit les appels publics, paramètres, retours et contraintes. `operational_contract()` résout ces informations avec la sémantique de sortie, les erreurs attendues et la preuve associée.

```python
from gallica import capabilities, operational_contract

for capability in capabilities():
    print(capability["id"], capability["call"])

contract = operational_contract("page_alto")
print(contract["services"])
print(contract["freshness"])
```

### Preuves live et attestations

Les déclarations de preuve checked-in ne contiennent plus de timestamp ou de run historique présenté comme état courant. Pendant la suite live, chaque preuve enregistre une observation réelle avec un `service_outcome` distinct du résultat pytest :

- `operational` si le service a effectivement répondu selon le contrat ;
- `environment-limited` si le test passe parce que le SDK a correctement identifié une limitation amont reproductible, par exemple un challenge anti-bot ou une réponse HTML/403.

Après succès de la suite complète, la CI génère `evidence-attestation.json`, lié au commit et au run exacts. Les attestations 2.0 séparent `test_outcome` et `service_outcome` ; les anciennes attestations 1.0 restent lisibles sans être promues artificiellement en preuve d'opérabilité.

```python
from gallica import load_evidence_attestation, operational_contract

attestation = load_evidence_attestation("evidence-attestation.json")
contract = operational_contract("page_alto", attestation=attestation)
print(contract["freshness"])
```

Documentation agent : [`docs/agents.md`](docs/agents.md). Modèle de preuve : [`docs/evidence.md`](docs/evidence.md).

## Quotas, validation des réponses et erreurs

Le transport partagé centralise throttling, retries bornés et `Retry-After`. Un HTTP 200 n'est pas accepté aveuglément : ALTO, IIIF et réponses structurées sont validés avant d'être exposés.

`.texteBrut` peut légitimement être servi en HTML, mais certains runners publics sont redirigés vers un challenge anti-bot. Le SDK détecte ce cas et le service reste explicitement `environment-limited` dans la référence.

Voir [`docs/quotas.md`](docs/quotas.md) et [`docs/errors.md`](docs/errors.md).

## Notebooks exécutables

Trois notebooks de référence sont exécutés en CI contre Gallica public :

- [`notebooks/01_search_and_metadata.ipynb`](notebooks/01_search_and_metadata.ipynb) : SRU + métadonnées OAIRecord ;
- [`notebooks/02_resumable_corpus.ipynb`](notebooks/02_resumable_corpus.ipynb) : corpus minimal + reprise ;
- [`notebooks/03_document_structure_and_iiif.ipynb`](notebooks/03_document_structure_and_iiif.ipynb) : Pagination, Toc, IIIF Presentation et IIIF Image `info.json`.

```bash
python -m pip install -e '.[docs]'
python scripts/execute_notebooks.py
```

## Surface publique actuelle

La frontière de compatibilité Python auditée pour la future série 0.2 est documentée dans [`docs/public-api.md`](docs/public-api.md). `gallica.__all__`, les champs des modèles de résultat et les signatures des principales méthodes publiques sont vérifiés en CI afin qu'une rupture accidentelle devienne un échec explicite.

La partie mécanique de cette section est générée depuis `capabilities()`. Une nouvelle capacité canonique ajoutée au code sans régénération de la documentation fait échouer la CI.

### Capacités canoniques

<!-- BEGIN GENERATED: canonical-capabilities -->
```text
Gallica.document(ark) -> Document
Gallica.periodical(ark) -> Periodical
Gallica.corpus(arks) -> Corpus
Gallica.search(query, start_record=1, maximum_records=50) -> SearchResults
Gallica.categories(query) -> Categories
Gallica.search_all(query, limit=None, page_size=50) -> Iterator[DublinCoreRecord]
Document.metadata() -> DocumentMetadata
Document.pagination() -> Pagination
Document.page_count() -> int
Document.toc() -> TocDocument
Document.iiif_manifest() -> IIIFPresentationManifest
Document.text() -> str
Document.search_text(query, page=None, start_result=None) -> ContentSearchResults
Document.search_text_all(query, page=None, limit=None) -> Iterator[ContentSearchItem]
Page.text() -> str
Page.alto() -> bytes
Page.iiif_info() -> IIIFImageInfo
Page.image(width=1000, fmt='jpg') -> bytes
Periodical.issue(when) -> Document | None
Corpus.fetch(output, metadata=True, text=False, alto=False, images=False, views=None, image_width=1000, resume=True) -> CorpusReport
```
<!-- END GENERATED: canonical-capabilities -->

### Référence, preuves et helpers publics

```text
__version__ -> str
programmable_reference() -> ReferenceSpec
capabilities() -> tuple[CapabilitySpec, ...]
operational_contracts(attestation=...) -> tuple[OperationalContract, ...]
operational_contract(id, attestation=...) -> OperationalContract
evidence() -> tuple[EvidenceSpec, ...]
capability_evidence() -> tuple[CapabilityEvidence, ...]
build_evidence_attestation(...) -> EvidenceAttestation
load_evidence_attestation(path) -> EvidenceAttestation
evidence_freshness(attestation=...) -> tuple[EvidenceFreshness, ...]
Gallica.capabilities() -> tuple[CapabilitySpec, ...]
SearchResults.arks -> tuple[str, ...]
SearchResults.write_jsonl() -> Path
ContentSearchMatch -> OCR rectangle
CorpusItemResult.failure_details -> tuple[CorpusArtifactFailure, ...]
CorpusItemResult.retryable -> bool
CorpusReport.retryable -> tuple[CorpusItemResult, ...]
```

La matrice humaine générée avec services, statuts et contraintes se trouve dans [`docs/capabilities.md`](docs/capabilities.md).

## Validation

```bash
ruff check src tests
mypy src/gallica
python scripts/generate_docs.py --check
pytest -m 'not live'
pytest -m live tests/test_live.py tests/test_live_usability.py
python scripts/execute_notebooks.py
```

La CI couvre Python 3.11 à 3.14, Ruff, mypy strict, documentation générée, couverture déterministe, wheel/sdist avec réinstallation, Windows/macOS, tests Gallica publics, attestations de preuve et notebooks.

## Documentation

- [`docs/getting-started.md`](docs/getting-started.md) : démarrage rapide ;
- [`docs/search.md`](docs/search.md) : SRU, Categories, pagination et JSONL ;
- [`docs/documents.md`](docs/documents.md) : métadonnées, Pagination, Toc, OCR, ALTO et IIIF ;
- [`docs/periodicals.md`](docs/periodicals.md) : numéros datés ;
- [`docs/corpus.md`](docs/corpus.md) : reprise, manifest et erreurs par artefact ;
- [`docs/quotas.md`](docs/quotas.md) : throttling et quotas ;
- [`docs/errors.md`](docs/errors.md) : erreurs et limitations ;
- [`docs/cli.md`](docs/cli.md) : CLI JSON-first ;
- [`docs/architecture.md`](docs/architecture.md) : architecture et non-objectifs ;
- [`docs/capabilities.md`](docs/capabilities.md) : matrice générée des capacités ;
- [`docs/public-api.md`](docs/public-api.md) : frontière publique auditée et politique de compatibilité ;
- [`docs/agents.md`](docs/agents.md) : consommation par agents ;
- [`docs/evidence.md`](docs/evidence.md) : preuves et attestations ;
- [`docs/release-readiness.md`](docs/release-readiness.md) : préparation de release ;
- [`docs/releasing.md`](docs/releasing.md) : procédure de release ;
- [`AGENTS.md`](AGENTS.md) : contraintes pour agents de développement.

## Non-objectifs actuels

Le SDK n'expose pas encore :

- PDF automatisé, faute de contrat public reproductible validé ;
- sélection implicite de toutes les vues ;
- export Parquet / DataFrame intégré ;
- parallélisme ou API async ;
- MCP.

Ces absences sont intentionnelles : le projet préfère une petite surface vérifiée à une collection d'URLs enveloppées à moitié, activité humaine déjà suffisamment représentée sur GitHub.

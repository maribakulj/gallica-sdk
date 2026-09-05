# gallica-sdk

`gallica-sdk` est une couche de référence programmable et vérifiée pour accéder aux services publics Gallica.

Le projet fournit deux artefacts liés :

1. un SDK Python léger pour notebooks, scripts et pipelines ;
2. une représentation machine-readable des capacités, contraintes, services et preuves Gallica afin qu'un agent puisse raisonner sur une base validée plutôt que reconstruire l'API à chaque session.

Le projet ne crée pas une nouvelle API réseau et ne remplace pas la documentation BnF. Les services publics et la documentation BnF restent l'autorité ; `gallica-sdk` fournit une connaissance opérationnelle testée de leur utilisation.

## Statut

**0.2.0.dev0 — corpus reprenable avec provenance, recherche paginée, packaging vérifié, CLI JSON, référence programmable, contrats opérationnels résolus, attestations CI et notebooks exécutés.**

Aucune release stable n'est encore publiée. Le dépôt prépare sa première release publique.

## Démarrage

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e .
```

Python 3.11+ est requis.

```python
from gallica import Gallica

with Gallica() as gallica:
    document = gallica.document("ark:/12148/bpt6k5738219s")
    metadata = document.metadata()
    print(metadata.record.title)
    print(document.page_count())
```

Guide : [`docs/getting-started.md`](docs/getting-started.md).

## Recherche

```python
with Gallica() as gallica:
    results = gallica.search('gallica all "Verdun"', maximum_records=10)
    for record in results:
        print(record.ark, record.title)
```

Pour parcourir plusieurs pages sans manipuler `startRecord` :

```python
with Gallica() as gallica:
    for record in gallica.search_all('gallica all "Verdun"', limit=200, page_size=50):
        print(record.ark, record.title)
```

Les champs Dublin Core restent répétables et le XML source est conservé dans `raw_xml`. Guide : [`docs/search.md`](docs/search.md).

## Documents et pages

```python
with Gallica() as gallica:
    document = gallica.document("bpt6k5460422k")
    text = document.text()
    matches = document.search_text("hugo")

    for item in document.search_text_all("hugo", limit=25):
        print(item.page_id)

    geometry = document.search_text("hugo", page=173)
    for match in geometry.items[0].matches:
        print(match.hpos, match.vpos, match.width, match.height)

    page = document.page(3)
    alto = page.alto()
    info = page.iiif_info()
    image = page.image(width=1000)
```

`ContentSearch` conserve les extraits HTML, les dimensions master et toutes les boîtes OCR retournées pour une vue. Guide : [`docs/documents.md`](docs/documents.md).

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

Les écritures sont atomiques. La reprise vérifie fingerprint de requête, taille et SHA-256 au lieu de considérer qu'un fichier présent est nécessairement valable. Les erreurs sont isolées par artefact : un échec de métadonnée n'empêche pas un ALTO ou une image indépendants du même ARK, et les succès partiels restent réutilisables au prochain `resume`. Le manifest conserve également paramètres, version SDK et provenance des échecs. Guide : [`docs/corpus.md`](docs/corpus.md).

## CLI

Le package installe une CLI volontairement mince, JSON-first, qui réutilise le même SDK plutôt que réimplémenter une seconde logique réseau :

```bash
gallica capabilities
gallica contract page_alto
gallica search 'gallica all "Verdun"' --maximum-records 5
gallica metadata bpt6k5738219s
gallica page-count bpt6k5738219s
```

Elle est testée après installation isolée du wheel et du sdist. Guide : [`docs/cli.md`](docs/cli.md).

## Référence programmable

Un agent n'a pas besoin d'installer le package pour découvrir le périmètre déclaré :

```text
reference/
├── gallica-reference.json
└── schema.json
```

Le manifeste est actuellement en `schema_version: 2.0`. Il expose les services, l'index des capacités, les preuves live, leur provenance historique et les invariants du projet, ainsi que les commandes d'export des contrats détaillés et opérationnels. Le JSON checked-in est validé réellement contre son JSON Schema en CI.

### Contrat minimal

`capabilities()` fournit la surface compacte : appel Python, paramètres, type de retour et contraintes.

```python
from gallica import capabilities

for capability in capabilities():
    print(capability["id"], capability["call"])
```

### Contrat opérationnel résolu

Pour un agent qui doit décider comment exécuter réellement une opération, `operational_contract()` résout en une structure unique :

- signature et paramètres ;
- contraintes ;
- sémantique de sortie ;
- media type source ;
- erreurs attendues ;
- services Gallica concernés ;
- preuves live ;
- fraîcheur de ces preuves ;
- exemple lié lorsqu'il existe.

Sans attestation CI explicite, la fraîcheur live est `unknown` : un vieux timestamp checked-in n'est plus présenté comme état courant. Une attestation générée après succès des tests live peut être chargée et fournie au contrat :

```python
from gallica import load_evidence_attestation, operational_contract

attestation = load_evidence_attestation("evidence-attestation.json")
contract = operational_contract("page_alto", attestation=attestation)
print(contract["freshness"])
```

La CI génère `evidence-attestation.json` uniquement après réussite de la suite live et l'archive comme artefact GitHub Actions. Un workflow séparé revalide ces preuves chaque semaine même en l'absence de nouveau commit.

Tous les contrats peuvent être exportés en JSON :

```bash
python scripts/export_capabilities.py > capabilities.json
python scripts/export_operational_contracts.py > operational-contracts.json
python scripts/export_reference.py > reference.json
```

Le contrat opérationnel est assemblé depuis les sources canoniques existantes. Il ne constitue pas une seconde vérité indépendante qui recopierait services et preuves.

Documentation agent : [`docs/agents.md`](docs/agents.md). Preuves, attestations et fraîcheur : [`docs/evidence.md`](docs/evidence.md).

## Quotas et erreurs

Le transport partagé centralise les retries, `Retry-After` et les buckets de throttling. Il rejoue aussi les erreurs réseau transitoires de manière bornée. Un HTTP 200 n'est pas accepté aveuglément : ALTO, IIIF et réponses structurées sont validés sémantiquement.

`.texteBrut` a un comportement particulier : sa représentation publique peut légitimement être HTML, mais les runners publics peuvent être redirigés vers un challenge anti-bot. Le SDK détecte ce challenge au lieu de l'enregistrer comme OCR et le service est donc déclaré `environment-limited` dans la référence.

- quotas : [`docs/quotas.md`](docs/quotas.md) ;
- erreurs et limitations : [`docs/errors.md`](docs/errors.md).

## Notebooks exécutables

Deux notebooks de référence sont exécutés réellement en CI contre Gallica public :

- [`notebooks/01_search_and_metadata.ipynb`](notebooks/01_search_and_metadata.ipynb) : SRU + métadonnées OAIRecord ;
- [`notebooks/02_resumable_corpus.ipynb`](notebooks/02_resumable_corpus.ipynb) : corpus minimal + preuve de reprise sans nouveau téléchargement.

Pour les exécuter localement :

```bash
python -m pip install -e '.[docs]'
python scripts/execute_notebooks.py
```

## PDF

Le SDK ne fournit pas `pdf()`. Les formes historiques `f1n1.pdf` et `f1.pdf` testées le 2 septembre 2026 ont répondu HTTP 200 avec du HTML depuis un runner GitHub public. PDF reste donc explicitement `not-supported` tant qu'un contrat automatisable reproductible n'est pas établi.

## Surface publique actuelle

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
Gallica.search() -> SearchResults
Gallica.search_all() -> Iterator[DublinCoreRecord]
Gallica.document() -> Document
Gallica.periodical() -> Periodical
Gallica.corpus() -> Corpus
SearchResults.arks -> tuple[str, ...]
SearchResults.write_jsonl() -> Path
ContentSearchMatch -> OCR rectangle
Document.metadata() -> DocumentMetadata
Document.page_count() -> int
Document.text() -> str
Document.search_text() -> ContentSearchResults
Document.search_text_all() -> Iterator[ContentSearchItem]
Document.page() -> Page
Page.text() -> str
Page.alto() -> bytes
Page.iiif_info() -> dict
Page.image() -> bytes
Periodical.issue() -> Document | None
Corpus.fetch() -> CorpusReport
CorpusItemResult.failure_details -> tuple[CorpusArtifactFailure, ...]
CorpusItemResult.retryable -> bool
CorpusReport.retryable -> tuple[CorpusItemResult, ...]
```

## Validation

```bash
ruff check src tests
mypy src/gallica
pytest -m 'not live'
pytest -m live tests/test_live.py tests/test_live_usability.py
python scripts/execute_notebooks.py
```

La CI exécute Python 3.11, 3.12, 3.13 et 3.14, Ruff, mypy strict, tests déterministes, validation JSON Schema, wheel/sdist avec réinstallation, smoke tests Windows/macOS, smoke tests Gallica publics, attestations de preuve et notebooks de référence. Le workflow `Live evidence` relance les tests publics chaque semaine.

## Documentation

- [`docs/getting-started.md`](docs/getting-started.md) : démarrage rapide ;
- [`docs/search.md`](docs/search.md) : SRU, pagination et JSONL ;
- [`docs/documents.md`](docs/documents.md) : métadonnées, OCR, ALTO et IIIF ;
- [`docs/periodicals.md`](docs/periodicals.md) : numéros datés ;
- [`docs/corpus.md`](docs/corpus.md) : reprise, manifest et erreurs par artefact ;
- [`docs/quotas.md`](docs/quotas.md) : comportement réseau et throttling ;
- [`docs/errors.md`](docs/errors.md) : erreurs et limitations ;
- [`docs/cli.md`](docs/cli.md) : CLI JSON-first ;
- [`docs/architecture.md`](docs/architecture.md) : architecture et non-objectifs ;
- [`docs/capabilities.md`](docs/capabilities.md) : matrice humaine des capacités ;
- [`docs/agents.md`](docs/agents.md) : usage par agents ;
- [`docs/evidence.md`](docs/evidence.md) : preuves, attestations et fraîcheur ;
- [`docs/release-readiness.md`](docs/release-readiness.md) : préparation de release ;
- [`docs/releasing.md`](docs/releasing.md) : procédure de release ;
- [`AGENTS.md`](AGENTS.md) : contraintes pour agents de développement.

Le dépôt `maribakulj/maj-scripts-api.bnf.fr` sert de source d'apprentissage sur les wrappers historiques et leurs défauts. `gallica-sdk` n'en dépend pas et ne reprend pas leur architecture legacy.

## Pas encore dans la 0.2

- accès PDF automatisé ;
- sélection implicite de toutes les vues ;
- export Parquet / DataFrame intégré ;
- parallélisme / async ;
- MCP.

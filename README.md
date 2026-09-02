# gallica-sdk

`gallica-sdk` est une bibliothèque Python légère pour accéder directement aux API publiques Gallica avec une interface cohérente, typée et testable.

Le projet ne crée pas une nouvelle API réseau. Il fournit une façade Python mince au-dessus des services Gallica pour les développeurs, notebooks, pipelines et outils automatisés.

## Statut

**0.1.0.dev0 — Phase 1 / accès documentaire.**

Le SDK couvre maintenant recherche SRU, métadonnées, pagination, OCR ALTO et texte brut, IIIF, recherche dans OCR, résolution de numéros de périodiques et PDF d'une vue. Les outils de corpus restent volontairement différés jusqu'à stabilisation complète de ces primitives.

## Installation de développement

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

Python 3.11+ est requis.

## Usage documentaire

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

Texte et recherche OCR :

```python
from gallica import Gallica

with Gallica() as g:
    doc = g.document("bpt6k5460422k")

    text = doc.text()
    first_page_text = doc.page(1).text()
    matches_xml = doc.search_text("hugo", start_result=1)
```

PDF d'une vue :

```python
from gallica import Gallica

with Gallica() as g:
    pdf = g.document("bc6p06zq4dn").page(1).pdf()
```

Le SDK n'annonce pas encore le téléchargement PDF multi-vues ou du document complet. Lors de la validation publique du 2 septembre 2026, le qualifier historique `f1n1.pdf` utilisé par d'anciens wrappers a renvoyé une page HTML plutôt qu'un flux PDF. La forme `fN.pdf` est, elle, testée en direct avant d'être exposée par `Page.pdf()`.

Périodiques :

```python
from datetime import date
from gallica import Gallica

with Gallica() as g:
    issue = g.periodical("cb32798952c").issue(date(1937, 3, 25))
    if issue is not None:
        print(issue.ark)
```

Recherche SRU :

```python
from gallica import Gallica

with Gallica() as g:
    xml = g.search('gallica all "Verdun"', maximum_records=10)
```

Le SRU, OAIRecord et ContentSearch retournent encore volontairement leur XML brut. Les modèles structurés ne seront ajoutés qu'après cartographie suffisante des formes de réponses réelles afin de ne pas figer trop tôt une abstraction incorrecte.

## Surface publique actuelle

```text
Gallica.search()
Gallica.document()
Gallica.periodical()
Document.metadata()
Document.page_count()
Document.text()
Document.search_text()
Document.page()
Page.text()
Page.alto()
Page.pdf()
Page.iiif_info()
Page.image()
Periodical.issue()
```

`Page.image()` utilise une largeur prudente de 1000 px par défaut. Les requêtes de largeur supérieure à 1000 px sont classées dans le bucket haute définition et limitées par le transport.

Les appels `.texteBrut` utilisent un bucket de 12,5 secondes et les PDF un bucket de 15,5 secondes, afin de rester sous les quotas publics documentés de 5/minute et 4/minute. Les réponses 429 et erreurs serveur transitoires sont retentées de manière bornée et `Retry-After` est respecté lorsqu'il est numérique.

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
- [`docs/capabilities.md`](docs/capabilities.md) : matrice des API Gallica connues, contraintes et statut d'intégration.

Le dépôt `maribakulj/maj-scripts-api.bnf.fr` sert de source d'apprentissage sur les wrappers historiques et leurs défauts. `gallica-sdk` n'en dépend pas et ne reprend pas son architecture legacy.

## Pas encore dans la 0.1

- modèles structurés SRU/OAIRecord/ContentSearch ;
- PDF multi-vues / document complet ;
- outils de corpus et reprise ;
- DataFrame / Parquet ;
- CLI ;
- MCP ;
- async.

Ces fonctionnalités seront ajoutées par tranches verticales après validation des primitives déjà présentes.

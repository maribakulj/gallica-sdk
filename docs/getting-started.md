# Démarrage rapide

## Installation de développement

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -e .
```

Python 3.11 ou supérieur est requis.

## Premier document

```python
from gallica import Gallica

with Gallica() as gallica:
    document = gallica.document("ark:/12148/bpt6k5738219s")
    metadata = document.metadata()

    print(metadata.record.title)
    print(document.page_count())
```

`Gallica.document()` n'effectue pas de requête réseau : il normalise l'ARK et retourne une façade légère. Les appels comme `metadata()`, `text()` ou `page_count()` interrogent ensuite les services publics Gallica.

## Première recherche

```python
with Gallica() as gallica:
    results = gallica.search('gallica all "Verdun"', maximum_records=10)

for record in results:
    print(record.ark, record.title)
```

Les champs Dublin Core sont répétables. Utilisez `record.values("creator")` plutôt que de supposer qu'un champ n'a qu'une seule valeur.

## Une page

```python
with Gallica() as gallica:
    page = gallica.document("bpt6k5619759j").page(1)
    alto = page.alto()
    image = page.image(width=1000)
```

Les vues Gallica exposées par le SDK sont numérotées à partir de 1.

## Un corpus reprenable

```python
with Gallica() as gallica:
    report = gallica.corpus(["bpt6k5738219s", "bpt6k5460422k"]).fetch(
        "./corpus",
        metadata=True,
        text=True,
        resume=True,
    )

for failure in report.failures:
    print(failure.ark, failure.error)
```

Le traitement continue après une erreur ordinaire sur un ARK. Avec `resume=True`, les artefacts déjà présents ne sont pas téléchargés une nouvelle fois.

## Vérifier ce qui est réellement supporté

```python
from gallica import capabilities, evidence_freshness, programmable_reference

print(programmable_reference()["schema_version"])
print([item["id"] for item in capabilities()])
print(evidence_freshness())
```

La référence programmable distingue les capacités supportées des comportements non validés. PDF, par exemple, reste volontairement non supporté.

## Suite

- [`search.md`](search.md) : SRU, pagination et JSONL ;
- [`documents.md`](documents.md) : métadonnées, OCR, ALTO et IIIF ;
- [`periodicals.md`](periodicals.md) : résolution datée des numéros ;
- [`corpus.md`](corpus.md) : reprise et manifest ;
- [`quotas.md`](quotas.md) : throttling et limites réseau ;
- [`errors.md`](errors.md) : stratégie d'erreurs et limitations.

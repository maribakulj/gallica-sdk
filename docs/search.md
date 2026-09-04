# Recherche SRU

## Une page de résultats

```python
from gallica import Gallica

with Gallica() as gallica:
    results = gallica.search(
        'gallica all "Victor Hugo"',
        maximum_records=20,
    )

print(results.total)
print(results.arks)
```

`maximum_records` est limité à 50 afin de respecter le contrat SRU utilisé par le SDK.

## Dublin Core répétable

Un résultat est un `DublinCoreRecord`. Les propriétés peuvent apparaître plusieurs fois :

```python
for record in results:
    print(record.title)
    print(record.values("creator"))
    print(record.values("date"))
```

`record.ark` fournit l'ARK normalisé lorsqu'un identifiant exploitable est présent.

## Pagination paresseuse

Pour parcourir plus d'une page :

```python
with Gallica() as gallica:
    for record in gallica.search_all(
        'gallica all "Victor Hugo"',
        limit=200,
        page_size=50,
    ):
        print(record.ark, record.title)
```

`search_all()` ne charge pas toutes les notices à l'avance. Les pages SRU sont demandées au fur et à mesure de l'itération.

## Recherche vers corpus

```python
with Gallica() as gallica:
    results = gallica.search('gallica all "Verdun"', maximum_records=20)
    report = gallica.corpus(results.arks).fetch(
        "./verdun-corpus",
        metadata=True,
        text=False,
        resume=True,
    )
```

Cette composition est volontairement directe : les résultats de recherche fournissent les ARK dont `Corpus` a besoin.

## Export JSONL

```python
results.write_jsonl("./results.jsonl")
```

Chaque ligne conserve les valeurs Dublin Core sous forme de listes et ajoute l'ARK normalisé lorsqu'il existe.

## Accès au XML source

La représentation structurée n'empêche pas les usages avancés :

```python
xml = results.raw_xml
```

Le XML original doit être utilisé lorsqu'un champ SRU n'est pas encore promu dans les modèles typés.

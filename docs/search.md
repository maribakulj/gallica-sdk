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

## Affiner une recherche avec Categories

Le service `Categories` agrège une requête CQL et renvoie les valeurs utilisables pour affiner la recherche :

```python
with Gallica() as gallica:
    facets = gallica.categories('gallica all "Victor Hugo"')

for item in facets.for_category("language"):
    print(item.display_value, item.approximate_count, item.cql_field)
```

Un `CategoryValue` conserve quatre informations distinctes : le nom du critère Categories, la `clean_value` fournie pour l'affinage, le libellé d'affichage éventuel et `approximate_count`.

Le mot *approximate* est volontaire : la documentation BnF indique que `howMany` est une estimation du moteur et que le nombre de résultats après affinage peut différer. Le SDK ne transforme donc pas cette valeur en un faux total exact.

Le service retourne au plus 20 valeurs par critère. Certains critères comme `language`, `provenance`, `date` et `creator` peuvent donc être incomplets. Les catégories plus fermées comme `typedoc`, `free_access` et `nqamoyen` sont documentées comme exhaustives dans ce cadre.

Le nom du critère Categories n'est pas toujours le champ CQL correspondant. Le SDK expose le mapping officiel via `item.cql_field` et `CATEGORY_CQL_FIELDS`, par exemple :

```python
language.cql_field   # "dc.language"
typedoc.cql_field    # "dc.type"
creator.cql_field    # "dc.creator"
```

Une catégorie inconnue reste conservée mais son `cql_field` vaut `None` : le SDK préfère signaler qu'il ne connaît pas le mapping plutôt que d'en inventer un.

`facets.raw_json` conserve la réponse JSON originale.

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

# Documents et pages

## Créer une façade Document

```python
from gallica import Gallica

with Gallica() as gallica:
    document = gallica.document("ark:/12148/bpt6k5738219s")
```

Le constructeur normalise l'ARK mais n'effectue pas encore de requête réseau.

## Métadonnées

```python
metadata = document.metadata()
print(metadata.record.title)
print(metadata.record.values("creator"))
print(metadata.indexing_mode)
print(metadata.ocr_quality)
```

`DocumentMetadata.raw_xml` conserve la réponse OAIRecord originale.

## Structure et pagination

Pour obtenir uniquement le nombre de vues image :

```python
count = document.page_count()
```

Pour exploiter la structure complète retournée par le service Pagination :

```python
pagination = document.pagination()

print(pagination.image_views)
print(pagination.first_displayed_page)
print(pagination.has_toc)
print(pagination.toc_location)

for page in pagination.pages:
    print(page.order, page.number, page.pagination_type, page.legend)
```

`Pagination` expose notamment les informations de navigation du document, le nombre de vues image/audio et, lorsqu'elles sont présentes, les étiquettes de pagination logique de chaque vue. `Document.page_count()` est volontairement une simple projection de `Pagination.image_views` : il n'existe pas un second contrat Pagination caché uniquement pour compter les pages.

Le XML d'origine reste disponible dans `pagination.raw_xml`.

## Table des matières

```python
toc = document.toc()
print(toc.format)
print(toc.well_formed)
print(toc.raw[:200])
```

Le service Gallica possède deux représentations historiques : certaines numérisations renvoient une table des matières HTML, d'autres une représentation TEI. Le SDK les distingue donc explicitement :

```python
if toc.format == "html":
    # contenu HTML historique ; well_formed vaut None
    ...
elif toc.format == "tei" and toc.well_formed:
    # TEI directement parsable comme XML
    ...
elif toc.format == "tei":
    # TEI identifiable mais XML amont mal formé ; le brut est préservé
    ...
```

Le SDK ne force pas HTML et TEI dans un modèle commun potentiellement destructeur. Il ne répare pas non plus silencieusement un TEI mal formé : `toc.raw` conserve exactement la représentation reçue et `toc.well_formed` indique si cette représentation TEI est directement parsable. Cette distinction est nécessaire parce que le service public peut actuellement livrer un document explicitement TEI dont le XML n'est pas strictement bien formé.

`pagination.has_toc` et `pagination.toc_location` permettent de savoir si le service Pagination signale une table des matières et à quelle vue elle est associée, sans télécharger le TOC lui-même.

## OCR texte brut

```python
text = document.text()
```

Le transport applique automatiquement le throttling conservateur associé à `.texteBrut`.

## Recherche dans l'OCR

Une recherche sans page retourne les pages contenant le terme ainsi qu'un extrait HTML surligné :

```python
matches = document.search_text("hugo")
print(matches.total)

for item in matches:
    print(item.page_id, item.content_html)
```

Le service public retourne au maximum 10 éléments par réponse. Pour parcourir davantage de résultats sans gérer `startResult` manuellement :

```python
for item in document.search_text_all("hugo", limit=25):
    print(item.page_id)
```

L'itérateur est paresseux et ne demande une nouvelle page de résultats que lorsqu'elle est nécessaire.

Pour localiser les occurrences OCR sur une vue précise, utiliser le numéro d'ordre de page attendu par ContentSearch :

```python
result = document.search_text("hugo", page=173)
item = result.items[0]
print(item.page_width, item.page_height)

for match in item.matches:
    print(match.alto_id, match.hpos, match.vpos, match.width, match.height)
```

`page_width` et `page_height` correspondent aux dimensions du fichier master. Chaque `ContentSearchMatch` représente un rectangle OCR dans ce même repère. Une page peut contenir plusieurs occurrences, elles sont donc conservées dans `item.matches` plutôt qu'aplaties en un unique rectangle.

`item.alto_id` reste disponible pour compatibilité avec les versions précédentes : il contient l'ancien texte direct de `<altoid>` lorsqu'il existe, ou l'identifiant de la première occurrence géométrique. Le XML ContentSearch d'origine reste disponible via `matches.raw_xml`.

## Pages

```python
page = document.page(3)
```

Les vues sont 1-based.

### Texte d'une vue

```python
page_text = page.text()
```

### ALTO

```python
alto_xml = page.alto()
```

Le SDK retourne les octets XML afin de ne pas imposer un modèle ALTO incomplet aux usages avancés.

### IIIF info.json

```python
info = page.iiif_info()
print(info["width"], info["height"])
```

### Image IIIF

```python
image_bytes = page.image(width=1000)
```

1000 px est la largeur prudente par défaut. Une largeur supérieure utilise le bucket réseau haute définition.

## PDF

Le SDK ne fournit pas `Document.pdf()` aujourd'hui. Les formes historiques testées ont retourné du HTML lors des validations automatisées publiques. La référence programmable marque donc PDF comme `not-supported` au lieu d'exposer une méthode dont le contrat serait incertain.

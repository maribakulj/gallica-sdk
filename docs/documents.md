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

## Nombre de vues

```python
count = document.page_count()
```

Le SDK utilise la structure retournée par le service Pagination et expose `nbVueImages` sous forme d'un entier.

## OCR texte brut

```python
text = document.text()
```

Le transport applique automatiquement le throttling conservateur associé à `.texteBrut`.

## Recherche dans l'OCR

```python
matches = document.search_text("hugo")
print(matches.total)

for item in matches:
    print(item.page_id, item.content_html)
```

Le XML ContentSearch d'origine reste disponible via `matches.raw_xml`.

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

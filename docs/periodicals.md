# Périodiques

`Gallica.periodical()` formalise uniquement les comportements spécifiques dont le SDK a un contrat validé. Le principal est la résolution d'un numéro à partir d'une date via le service `Issues`.

## Résoudre un numéro daté

```python
from datetime import date
from gallica import Gallica

with Gallica() as gallica:
    issue = gallica.periodical("cb32798952c").issue(date(1937, 3, 25))

if issue is not None:
    print(issue.ark)
    print(issue.metadata().record.title)
```

Le résultat est un `Document` normal. Une fois le numéro résolu, les mêmes primitives documentaires sont disponibles : métadonnées, texte, pages, ALTO et IIIF.

## Absence de résultat

`Periodical.issue()` retourne `None` lorsqu'aucun numéro correspondant n'est résolu par le service public.

## Pourquoi pas un énorme modèle Periodical ?

Le SDK n'invente pas une hiérarchie complète de volumes, fascicules, suppléments et séries tant qu'un cas d'usage et un contrat Gallica précis ne la justifient pas. Une abstraction plus riche pourra être ajoutée lorsque les usages réels le demanderont.

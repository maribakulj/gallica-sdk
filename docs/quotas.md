# Quotas et comportement réseau

Les services publics Gallica n'ont pas tous les mêmes contraintes. `gallica-sdk` centralise les comportements de retry et de throttling dans le transport partagé afin que chaque méthode ne réimplémente pas sa propre politique.

## Buckets actuels

| Bucket SDK | Usage | Intervalle conservateur |
|---|---|---:|
| `default` | SRU, OAIRecord, Pagination, Issues, ContentSearch, ALTO, IIIF standard | 0 s ajouté par le SDK |
| `text` | `.texteBrut` | 12,5 s |
| `iiif_hd` | image IIIF au-dessus de 1000 px | 12,5 s |

Le bucket `text` reste sous le quota public documenté de 5 requêtes par minute. Le bucket haute définition est volontairement conservateur.

## Retries

Le transport réessaie de manière bornée les statuts :

```text
429, 500, 502, 503, 504
```

`Retry-After` est respecté lorsqu'il est exploitable ; sinon un backoff borné est appliqué.

## Ce que le SDK ne fait pas

- il ne lance pas de parallélisme implicite ;
- il ne contourne pas les buckets pour accélérer un corpus ;
- il ne transforme pas `views=None` en téléchargement de toutes les pages ;
- il ne promet pas qu'un quota externe restera inchangé.

## Images IIIF

```python
page.image(width=1000)
```

1000 px est la valeur par défaut. Une largeur supérieure est classée dans le bucket HD par le SDK.

## Corpus

`Corpus.fetch()` réutilise exactement les mêmes primitives réseau. Il n'a pas de client HTTP parallèle ou de stratégie cachée qui permettrait de dépasser les limites du transport partagé.

## Provenance

Les contraintes importantes sont également exposées dans `capabilities()` et dans la référence programmable. Lorsqu'un comportement dépend d'un service externe, consultez `evidence_freshness()` pour vérifier l'âge de la dernière observation live enregistrée.

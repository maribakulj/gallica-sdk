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

Il réessaie également les erreurs de transport transitoires remontées par `httpx` (par exemple timeout ou coupure de connexion), toujours dans la limite du budget de retries configuré. Une erreur réseau encore présente après épuisement de ce budget remonte au code appelant.

`Retry-After` est respecté sous ses deux formes HTTP usuelles : nombre de secondes ou date HTTP. Lorsqu'il est absent ou inexploitable, un backoff exponentiel borné est utilisé.

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

## Validation des réponses

Un statut HTTP 200 n'est pas considéré comme une preuve suffisante de succès. La validation est spécifique à chaque service : ALTO doit être du XML ALTO, une image IIIF doit être une image et les réponses structurées principales doivent présenter leur structure minimale attendue.

`.texteBrut` constitue une exception importante : malgré son nom, sa représentation publique peut légitimement être HTML. Le SDK accepte cette représentation mais rejette explicitement le challenge anti-bot vers lequel les runners publics froids sont actuellement susceptibles d'être redirigés. Le service est donc déclaré `environment-limited` dans la référence programmable plutôt que `live-validated`.

## Corpus

`Corpus.fetch()` réutilise exactement les mêmes primitives réseau. Il n'a pas de client HTTP parallèle ou de stratégie cachée qui permettrait de dépasser les limites du transport partagé.

## Provenance

Les contraintes importantes sont également exposées dans `capabilities()` et dans la référence programmable. Lorsqu'un comportement dépend d'un service externe, consultez `evidence_freshness()` pour vérifier l'âge de la dernière observation live enregistrée.

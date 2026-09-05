# Erreurs et limitations

## Erreurs HTTP et réseau

Les méthodes réseau reposent sur `httpx`. Après les retries bornés du transport, une réponse HTTP non récupérable ou une erreur réseau persistante remonte sous forme d'exception plutôt que d'être transformée silencieusement en valeur vide.

Cette règle est importante : une absence de donnée et une panne réseau ne sont pas la même chose.

## Réponses HTTP 200 invalides

Gallica peut théoriquement répondre `HTTP 200` avec un contenu qui ne correspond pas à la ressource demandée. `gallica-sdk` vérifie désormais plusieurs contrats de contenu avant d'accepter la réponse.

Les erreurs détectées par cette validation remontent sous forme de :

```python
from gallica import GallicaResponseError
```

Exemples :

- page HTML renvoyée à la place d'un ALTO ;
- XML ALTO avec une racine inattendue ;
- page HTML renvoyée à la place d'une image IIIF ;
- `.texteBrut` qui répond avec du HTML ;
- SRU/OAIRecord/ContentSearch avec une structure XML incompatible ;
- `info.json` IIIF sans dimensions valides.

`GallicaResponseError` hérite de `GallicaError`. Cette première taxonomie reste volontairement petite ; elle distingue déjà une réponse externe sémantiquement invalide d'une simple absence de donnée.

## Entrées invalides

Le SDK valide les contraintes qu'il connaît avant de lancer certaines requêtes :

- ARK normalisable ;
- vues strictement positives ;
- tailles de page SRU dans la limite supportée ;
- vues explicites requises pour les téléchargements ALTO/images de `Corpus`.

## Corpus

`Corpus.fetch()` isole les erreurs ordinaires par ARK. Une erreur sur un document est enregistrée dans le rapport et le traitement continue sur les suivants.

```python
report = corpus.fetch("./corpus", metadata=True, resume=True)

for failure in report.failures:
    print(failure.ark, failure.error)
```

Les interruptions système ne sont pas absorbées. Le manifest, les écritures atomiques et les checksums permettent ensuite de reprendre le traitement sans approuver automatiquement un fichier présent sur disque.

## Valeur absente

Certaines opérations ont une absence de résultat normale. Par exemple :

```python
issue = periodical.issue(date_value)
```

peut retourner `None` lorsqu'aucun numéro n'est résolu.

## XML non modélisé

Les modèles structurés issus de SRU, OAIRecord et ContentSearch conservent `raw_xml`. Lorsqu'une information Gallica n'est pas encore représentée dans un champ typé, il faut utiliser la réponse source plutôt que supposer que l'information n'existe pas.

## Fonctionnalités volontairement non supportées

Une capacité absente n'est pas automatiquement un bug. PDF reste non supporté parce que les formes automatisées historiques testées n'ont pas produit un contrat reproductible. De même, le SDK ne propose pas de sélection implicite de toutes les pages.

La référence programmable est la meilleure source pour distinguer :

- capacité supportée ;
- service connu mais non supporté ;
- preuve live récente ou devenue stale.

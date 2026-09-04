# Erreurs et limitations

## Erreurs HTTP

Les méthodes réseau reposent sur `httpx`. Après les retries bornés du transport, une réponse HTTP non récupérable remonte sous forme d'exception plutôt que d'être transformée silencieusement en valeur vide.

Cette règle est importante : une absence de donnée et une panne réseau ne sont pas la même chose.

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

Les interruptions système ne sont pas absorbées. Le manifest et les écritures atomiques permettent ensuite de reprendre le traitement.

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

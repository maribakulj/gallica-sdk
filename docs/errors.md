# Erreurs et limitations

## Erreurs HTTP et réseau

Les méthodes réseau reposent sur `httpx`. Après les retries bornés du transport, une réponse HTTP non récupérable ou une erreur réseau persistante remonte sous forme d'exception plutôt que d'être transformée silencieusement en valeur vide.

Cette règle est importante : une absence de donnée et une panne réseau ne sont pas la même chose.

## Réponses HTTP 200 invalides

Gallica peut répondre `HTTP 200` avec un contenu qui ne correspond pas à la ressource demandée. `gallica-sdk` vérifie plusieurs contrats de contenu avant d'accepter la réponse.

Les erreurs détectées par cette validation remontent sous forme de :

```python
from gallica import GallicaResponseError
```

Exemples :

- page HTML renvoyée à la place d'un ALTO ;
- XML ALTO avec une racine inattendue ;
- page HTML renvoyée à la place d'une image IIIF ;
- SRU/OAIRecord/ContentSearch avec une structure XML incompatible ;
- `info.json` IIIF sans dimensions valides ;
- requête `.texteBrut` redirigée vers un challenge anti-bot Gallica.

### Particularité de `.texteBrut`

Le nom du qualifier est trompeur : le service public `.texteBrut` peut légitimement servir un document HTML contenant l'en-tête bibliographique et le texte OCR. Le SDK n'interprète donc pas `text/html` comme une erreur pour cette primitive.

Il distingue en revanche cette représentation légitime d'un challenge anti-bot identifié par l'URL finale ou des marqueurs spécifiques au challenge. Cette règle est volontairement spécifique à `.texteBrut` : pour ALTO ou une image IIIF, une page HTML reste une réponse invalide.

`GallicaResponseError` hérite de `GallicaError`. Cette première taxonomie reste volontairement petite ; elle distingue déjà une réponse externe sémantiquement invalide d'une simple absence de donnée.

## Entrées invalides

Le SDK valide les contraintes qu'il connaît avant de lancer certaines requêtes :

- ARK normalisable ;
- vues strictement positives ;
- tailles de page SRU dans la limite supportée ;
- vues explicites requises pour les téléchargements ALTO/images de `Corpus`.

## Corpus

`Corpus.fetch()` isole les erreurs au niveau de chaque artefact demandé. L'échec d'une métadonnée n'empêche donc pas, à lui seul, la récupération du texte, d'un ALTO ou d'une image pour le même ARK. Les artefacts réussis sont conservés dans le manifest et peuvent être réutilisés lors d'un `resume` ultérieur.

La compatibilité avec le rapport historique est conservée : `report.failures` renvoie toujours les items en erreur et `item.error` reste une chaîne de synthèse. Pour un traitement fiable, utilisez les détails structurés :

```python
report = corpus.fetch("./corpus", metadata=True, text=True, resume=True)

for item in report.failures:
    print(item.ark, item.retryable)
    for failure in item.failure_details:
        print(
            failure.kind,
            failure.path,
            failure.error_type,
            failure.message,
            failure.retryable,
        )
```

`report.retryable` renvoie les items en erreur qui contiennent au moins une panne classée comme transitoire. Cette classification est volontairement conservatrice : erreurs de transport `httpx` et statuts HTTP `429`, `500`, `502`, `503`, `504` sont retryables ; une erreur sémantique ou locale n'est pas automatiquement rejouable.

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

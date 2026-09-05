# Corpus

`Corpus` compose les primitives documentaires existantes du SDK. Il ne crée aucun nouveau transport réseau et reste synchrone afin que les quotas, retries et règles de throttling du client `Gallica` restent la source unique de vérité.

## Création

```python
from gallica import Gallica

with Gallica() as g:
    corpus = g.corpus([
        "bpt6k5738219s",
        "ark:/12148/bpt6k5460422k",
    ])
```

Les ARK sont normalisés, dédupliqués et conservent l'ordre de leur première apparition.

## Métadonnées et texte

```python
report = corpus.fetch(
    "./corpus",
    metadata=True,
    text=True,
    resume=True,
)
```

Pour chaque ARK :

```text
documents/<ark>/metadata.json
documents/<ark>/text.txt
```

`metadata.json` contient les champs Dublin Core structurés, `indexing_mode` et `ocr_quality` lorsqu'ils existent.

## ALTO et images

Les artefacts page par page exigent une liste explicite de vues :

```python
report = corpus.fetch(
    "./corpus",
    metadata=False,
    alto=True,
    images=True,
    views=[1, 2, 3],
    image_width=1000,
    resume=True,
)
```

Disposition :

```text
documents/<ark>/pages/1/alto.xml
documents/<ark>/pages/1/image.jpg
documents/<ark>/pages/2/alto.xml
documents/<ark>/pages/2/image.jpg
```

Les vues doivent être des entiers `>= 1`. Elles sont dédupliquées en conservant l'ordre. `alto=True` ou `images=True` sans `views` déclenche une `ValueError` : le SDK n'interprète jamais implicitement « toutes les pages ».

La largeur d'image par défaut est 1000 px. Au-delà de 1000 px, les appels passent par le bucket IIIF HD du transport.

## Reprise vérifiée

`resume=True` ne considère plus qu'un fichier existant est automatiquement valide. Chaque artefact demandé est associé à un fingerprint de requête et à une preuve d'intégrité enregistrée dans le manifest.

Pour être réutilisé, un artefact doit satisfaire simultanément :

- le même type de ressource et les mêmes paramètres de requête ;
- le même fingerprint de contrat ;
- la même taille en octets ;
- le même SHA-256 que lors de son écriture validée.

Par exemple, une image récupérée avec `image_width=800` n'est pas réutilisée si une exécution ultérieure demande `image_width=1000`, même si `image.jpg` existe encore au même chemin. Un fichier modifié ou tronqué est également récupéré à nouveau.

Un ancien `manifest.jsonl` ne contenant pas ces informations de provenance est traité comme non fiable pour la reprise : les artefacts sont régénérés avant d'être enregistrés dans le nouveau format.

Les fichiers texte et binaires sont d'abord écrits dans un fichier temporaire dans le même répertoire, puis remplacés atomiquement avec `os.replace`. Un fichier final n'est donc pas créé avant la fin de son écriture.

## Manifest

Chaque tentative réellement exécutée ajoute une ligne à :

```text
manifest.jsonl
```

Chaque ligne conserve les champs de rapport historiques et ajoute `artifacts`, contenant pour chaque ressource validée :

```json
{
  "kind": "image",
  "path": "documents/bpt6k5738219s/pages/1/image.jpg",
  "fingerprint": "...sha256...",
  "sha256": "...sha256 du contenu...",
  "size": 123456,
  "parameters": {
    "view": 1,
    "width": 1000,
    "format": "jpg"
  },
  "sdk_version": "0.2.0.dev0"
}
```

Le fingerprint représente la demande logique, pas le contenu. Le SHA-256 représente le contenu réellement écrit. Cette séparation permet de détecter à la fois un changement de paramètres et une corruption du fichier.

Une exécution entièrement `skipped` n'ajoute pas une nouvelle ligne, puisqu'aucune tentative réseau ou écriture n'a eu lieu.

## Erreurs

Une exception ordinaire sur un ARK produit un `CorpusItemResult(status="error")` et le traitement continue avec l'ARK suivant. Seuls les artefacts dont la provenance a été établie pendant l'exécution ou validée à partir du manifest sont signalés comme valides dans le résultat.

`KeyboardInterrupt`, `SystemExit` et les autres exceptions héritant directement de `BaseException` ne sont pas absorbées.

## Rapport

```python
report.successes
report.failures
report.skipped
report.items
report.manifest_path
```

Chaque élément est un `CorpusItemResult` avec :

```text
ark
status
metadata_path
text_path
alto_paths
image_paths
artifacts
error
```

`artifacts` contient des `CorpusArtifactRecord` avec fingerprint, checksum, taille, paramètres et version du SDK ayant produit l'artefact.

## Limites actuelles

La ligne 0.2 ne propose volontairement pas encore :

- sélection implicite de toutes les vues ;
- parallélisme ;
- async ;
- Parquet/DataFrame ;
- PDF ;
- téléchargement de manifests IIIF Presentation.

Ces fonctionnalités ne doivent être ajoutées que si elles conservent les garanties de reprise, de quotas et d'audit du manifest.

# Matrice de capacités

Cette page décrit le périmètre public actuel du SDK. La table centrale est générée depuis `capabilities()`, `capability_evidence()` et `programmable_reference()` afin que les signatures, services, retours et statuts ne dérivent pas de la surface réellement exposée.

Pour régénérer la table après une évolution du SDK :

```bash
python scripts/generate_docs.py
```

La CI exécute `python scripts/generate_docs.py --check` et échoue si le bloc généré n'est plus à jour.

## Capacités canoniques

<!-- BEGIN GENERATED: canonical-capabilities -->
| ID | Appel Python | Service | Retour | Statut | Contraintes canoniques |
|---|---|---|---|---|---|
| `document` | `Gallica.document(ark) -> Document` | none; local handle construction | `Document` | local | accepts bare identifiers, ark:/12148/... and canonical Gallica URLs |
| `periodical` | `Gallica.periodical(ark) -> Periodical` | none; local handle construction | `Periodical` | local | the ARK is normalized before use |
| `corpus` | `Gallica.corpus(arks) -> Corpus` | none; local corpus construction | `Corpus` | local | ARKs are normalized and deduplicated while preserving first-seen order |
| `search` | `Gallica.search(query, start_record=1, maximum_records=50) -> SearchResults` | SRU 1.2 | `SearchResults` | live-validated | maximum_records must be between 1 and 50 |
| `categories` | `Gallica.categories(query) -> Categories` | services/Categories | `Categories` | environment-limited | empty queries are rejected<br>the service returns at most 20 values per category<br>howMany counts are approximate<br>some categories are not exhaustive<br>raw JSON remains available as raw_json |
| `search_all` | `Gallica.search_all(query, limit=None, page_size=50) -> Iterator[DublinCoreRecord]` | SRU 1.2 | `Iterator[DublinCoreRecord]` | live-validated | page_size must be between 1 and 50<br>limit must be >= 1 when supplied<br>results are fetched lazily page by page |
| `document_metadata` | `Document.metadata() -> DocumentMetadata` | services/OAIRecord | `DocumentMetadata` | live-validated | raw XML remains available as raw_xml |
| `document_pagination` | `Document.pagination() -> Pagination` | services/Pagination | `Pagination` | live-validated | view orders are 1-based<br>raw XML remains available as raw_xml |
| `document_page_count` | `Document.page_count() -> int` | services/Pagination | `int` | live-validated | projects Pagination.image_views |
| `document_toc` | `Document.toc() -> TocDocument` | services/Toc | `TocDocument` | live-validated | returns format='html' for legacy TOCs and format='tei' for TEI XML<br>raw upstream content is preserved |
| `document_text` | `Document.text() -> str` | .texteBrut | `str` | environment-limited | public quota documented as 5 requests/minute |
| `content_search` | `Document.search_text(query, page=None, start_result=None) -> ContentSearchResults` | services/ContentSearch | `ContentSearchResults` | live-validated | page and start_result must be >= 1 when supplied<br>the public service returns at most 10 items per request<br>when page is supplied, OCR word rectangles are returned relative to p_width/p_height<br>raw XML remains available as raw_xml |
| `content_search_all` | `Document.search_text_all(query, page=None, limit=None) -> Iterator[ContentSearchItem]` | services/ContentSearch | `Iterator[ContentSearchItem]` | live-validated | page must be >= 1 when supplied<br>limit must be >= 1 when supplied<br>pagination is lazy and follows the service's 10-item page cap |
| `page_text` | `Page.text() -> str` | .texteBrut | `str` | environment-limited | public quota documented as 5 requests/minute |
| `page_alto` | `Page.alto() -> bytes` | RequestDigitalElement E=ALTO | `bytes` | live-validated | view numbers are 1-based |
| `page_iiif_info` | `Page.iiif_info() -> dict[str, object]` | IIIF Image info.json | `dict[str, object]` | live-validated | Image API is distinct from IIIF Presentation |
| `page_image` | `Page.image(width=1000, fmt='jpg') -> bytes` | IIIF Image | `bytes` | live-validated | width must be >= 1<br>width > 1000 uses the HD rate bucket<br>1000px is the recommended default |
| `periodical_issue` | `Periodical.issue(when) -> Document \| None` | services/Issues | `Document \| None` | live-validated | resolution uses dayOfYear from the Issues response |
| `corpus_fetch` | `Corpus.fetch(output, metadata=True, text=False, alto=False, images=False, views=None, image_width=1000, resume=True) -> CorpusReport` | composition of supported SDK primitives | `CorpusReport` | mixed: environment-limited, live-validated | ALTO or images require explicit views<br>there is no implicit all-pages mode<br>resume validates request fingerprint, byte size and SHA-256<br>ordinary per-artifact failures do not stop independent artifacts or later ARKs |
<!-- END GENERATED: canonical-capabilities -->

Le statut est lui aussi dérivé de la référence programmable. `local` signifie que la construction elle-même ne fait pas de requête réseau. `environment-limited` signifie que le SDK possède un contrat et un comportement testé, mais que l'accès public automatisé n'est pas reproductible depuis tous les runners. `mixed` apparaît pour une composition qui combine des services de statuts différents.

## Règle de statut

Une primitive réseau n'est pas annoncée `live-validated` uniquement parce que son URL est connue. Elle doit disposer d'une construction de requête testée, d'un parsing ou d'une validation déterministe, d'au moins une preuve live pertinente et d'une documentation de ses contraintes opérationnelles.

Depuis les attestations de preuve 2.0, le résultat du test et l'état observé du service sont séparés. Un test peut donc être `passed` tout en enregistrant `service_outcome=environment-limited`, par exemple lorsque Categories renvoie du HTML/403 ou lorsque `.texteBrut` déclenche un challenge anti-bot sur un runner public.

## Contrats structurés

Le SDK transforme seulement les structures suffisamment stables pour apporter une vraie valeur :

- SRU devient `SearchResults`, contenant le total et des `DublinCoreRecord` ;
- Categories devient `Categories`, avec valeurs typées, compte `howMany` explicitement approximatif, mapping vers les champs CQL lorsqu'il est connu et JSON source conservé ;
- OAIRecord devient `DocumentMetadata`, avec Dublin Core répétable, informations techniques Gallica et XML source ;
- Pagination devient `Pagination`, avec nombre de vues, structure de navigation, labels logiques par vue et XML source ;
- Toc devient `TocDocument` et conserve explicitement la différence entre anciens sommaires HTML et TEI XML ;
- ContentSearch devient `ContentSearchResults`, avec extraits, pagination, dimensions master et toutes les occurrences `ContentSearchMatch` lorsque la géométrie est demandée ;
- `ContentSearchItem.alto_id` reste disponible pour compatibilité et pointe vers la valeur historique directe ou la première occurrence géométrique.

Les modèles structurés conservent le payload amont brut (`raw_xml` ou `raw_json`) lorsque ce payload fait partie du contrat public.

## Corpus reprenable

`Gallica.corpus(arks)` normalise et déduplique les ARK en conservant l'ordre. `Corpus.fetch()` peut produire `metadata.json`, `text.txt`, `pages/<vue>/alto.xml` et `pages/<vue>/image.jpg` ainsi qu'un `manifest.jsonl` append-only pour les tentatives réellement exécutées.

Avec `resume=True`, la reprise vérifie le fingerprint de requête, la taille et le SHA-256 des artefacts. Un document partiel ne récupère que les fichiers manquants. Les écritures sont atomiques et les erreurs ordinaires sont isolées par artefact afin de ne pas interrompre les ARK ou artefacts indépendants.

ALTO et images exigent `views=[...]`. Cette contrainte est intentionnelle : le SDK ne transforme jamais une requête de page en téléchargement implicite de l'intégralité d'un document. Le corpus reste synchrone et passe par le transport partagé, sans canal parallèle contournant les quotas.

## Capacité explicitement non supportée

Le PDF n'est volontairement pas exposé par `capabilities()`. Les formes historiques testées depuis GitHub Actions le 2 septembre 2026 ont répondu HTTP 200 avec du HTML plutôt qu'un flux PDF. Le service reste donc `not-supported` dans la référence tant qu'un contrat automatisable reproductible n'est pas établi.

## Source de vérité opérationnelle

La table ci-dessus est une projection générée. Les sources canoniques restent :

- `capabilities()` pour appels, paramètres, retours et contraintes ;
- `programmable_reference()` / `reference/gallica-reference.json` pour les services et leurs statuts ;
- `capability_evidence()` pour les liens capacité → service → preuve ;
- `evidence()` pour les déclarations de preuve ;
- les attestations CI pour les observations datées et leur `service_outcome` ;
- `operational_contract()` pour la vue résolue destinée aux consommateurs automatisés.

La documentation BnF et les services publics Gallica restent l'autorité externe. Cette matrice décrit le contrat observé et vérifié par `gallica-sdk`, pas une nouvelle API officielle.

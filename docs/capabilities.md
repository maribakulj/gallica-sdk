# Matrice de capacités

Cette matrice décrit le périmètre public visé par le SDK et distingue les capacités connues des capacités effectivement livrées.

| Capacité | Service Gallica | Entrée principale | Sortie SDK | Contrainte connue | Statut |
|---|---|---|---|---|---|
| Recherche bibliographique | SRU 1.2 | requête CQL | `SearchResults` / `DublinCoreRecord` | `maximumRecords <= 50` | supportée |
| Métadonnées document | `services/OAIRecord` | ARK | `DocumentMetadata` | Dublin Core répétable + informations techniques Gallica | supportée |
| Pagination / nombre de vues | `services/Pagination` | ARK | `int` | `nbVueImages` est la source attendue | supportée |
| Résolution d'un numéro de périodique | `services/Issues` | ARK + date | `Document | None` | `dayOfYear` structuré | supportée |
| Recherche dans OCR | `services/ContentSearch` | ARK + requête | `ContentSearchResults` | pagination `startResult`, 10 éléments par réponse | supportée |
| OCR texte brut | `.texteBrut` | ARK / plage de vues | `str` | quota public documenté : 5/min | supportée |
| OCR ALTO | `RequestDigitalElement` | ARK + vue | `bytes` XML ALTO | vue obligatoire | supportée |
| Informations IIIF | IIIF `info.json` | ARK + vue | `dict` JSON | endpoint Image distinct de Presentation | supportée |
| Image IIIF | IIIF Image | ARK + vue | `bytes` image | `/full/full/` ou largeur >1000 px : classe HD ; quota public documenté | supportée, largeur prudente par défaut |
| PDF automatisé | représentation `.pdf` / qualifiers historiques | ARK / vue / plage | non exposé | quota public documenté : 4/min ; comportement automatisé à caractériser | non supportée pour l'instant |
| Corpus métadonnées/texte | composition SDK | liste d'ARK | `CorpusReport` + manifest + fichiers | réutilise les quotas du transport ; synchrone | supportée en 0.2 dev |
| Corpus ALTO/images | composition SDK | liste d'ARK + vues | à définir | volume, reprise et quotas à caractériser | différée |

## Règle de statut

Une ligne ne doit pas être annoncée comme « supportée » uniquement parce que l'URL est connue. Pour une primitive réseau, il faut :

1. une construction de requête couverte par test ;
2. une réponse simulée couvrant le parsing ou la valeur retournée ;
3. un smoke test live depuis un réseau public ;
4. une documentation de la contrainte de quota lorsqu'elle existe.

Pour une capacité de composition comme `Corpus`, il faut en plus des tests déterministes de reprise, d'écriture partielle et d'isolation des erreurs.

## Contrats structurés Phase 2

Le SDK transforme seulement les structures suffisamment stables pour apporter une vraie valeur :

- SRU devient `SearchResults`, contenant le total et des `DublinCoreRecord` ;
- les propriétés Dublin Core restent répétables et sont conservées sous forme de tuples ;
- OAIRecord devient `DocumentMetadata`, avec le Dublin Core, `mode_indexation`, `nqamoyen` lorsqu'ils existent, et le XML original ;
- ContentSearch devient `ContentSearchResults`, avec `total`, `query`, les items (`p_id`, extrait HTML, `altoid`, score) et le XML original.

Chaque modèle structuré conserve `raw_xml`. Cette décision évite de devoir choisir entre ergonomie et fidélité aux réponses Gallica, et permet d'ajouter plus tard des champs sans casser l'accès aux données non modélisées.

## Corpus Phase 3

`Gallica.corpus(arks)` normalise et déduplique les ARK en conservant l'ordre. `Corpus.fetch()` peut produire `metadata.json` et `text.txt` par document ainsi qu'un `manifest.jsonl` append-only pour les tentatives réellement exécutées.

La reprise ne repose pas sur la seule présence d'une ancienne ligne de manifest : elle vérifie les artefacts demandés. Avec `resume=True`, un document entièrement présent est sauté ; un document partiel ne récupère que les fichiers manquants. Les fichiers sont écrits via un fichier temporaire puis renommés atomiquement. Une exception ordinaire sur un ARK est enregistrée et le corpus continue ; les interruptions système ne sont pas absorbées.

La V1 reste synchrone et passe exclusivement par les primitives du SDK. Elle ne possède donc aucun transport parallèle susceptible de contourner les buckets de quotas existants.

## Choix d'interface documentaire

- `Document.text()` expose `.texteBrut` au niveau document.
- `Page.text()` demande exactement une vue via `.texteBrut`.
- `Document.search_text()` expose `ContentSearch` sous forme structurée.
- `Gallica.periodical(ark).issue(date)` formalise uniquement la résolution datée déjà portée par `Issues`; le résultat est un `Document` normal.

## PDF : résultat de la validation

Le PDF n'est volontairement pas exposé. Deux formes issues des usages historiques ont été testées depuis GitHub Actions le 2 septembre 2026 : `f1n1.pdf` et `f1.pdf`. Dans les deux cas, Gallica a répondu HTTP 200 avec `text/html;charset=UTF-8` plutôt qu'un flux commençant par `%PDF`. Le quota PDF public reste connu, mais ne suffit pas à établir un contrat d'accès automatisé reproductible.

## Sources de travail

Les contrats initiaux proviennent de la documentation publique api.bnf.fr et des validations réalisées dans `maribakulj/maj-scripts-api.bnf.fr`. Ce dépôt reste indépendant de son code : les connaissances sont reprises, pas son architecture ni ses adaptateurs legacy.

# Matrice de capacités

Cette matrice décrit le périmètre public visé par le SDK et distingue les capacités connues des capacités effectivement livrées.

| Capacité | Service Gallica | Entrée principale | Sortie native | Contrainte connue | Statut |
|---|---|---|---|---|---|
| Recherche bibliographique | SRU 1.2 | requête CQL | XML | `maximumRecords <= 50` | supportée |
| Métadonnées document | `services/OAIRecord` | ARK | XML | structure historique Gallica | supportée |
| Pagination / nombre de vues | `services/Pagination` | ARK | XML | `nbVueImages` est la source attendue | supportée |
| Résolution d'un numéro de périodique | `services/Issues` | ARK + date | XML | `dayOfYear` structuré | supportée |
| Recherche dans OCR | `services/ContentSearch` | ARK + requête | XML | pagination `startResult` | supportée |
| OCR texte brut | `.texteBrut` | ARK / plage de vues | texte | quota public documenté : 5/min | supportée |
| OCR ALTO | `RequestDigitalElement` | ARK + vue | XML ALTO | vue obligatoire | supportée |
| Informations IIIF | IIIF `info.json` | ARK + vue | JSON | endpoint Image distinct de Presentation | supportée |
| Image IIIF | IIIF Image | ARK + vue | image | `/full/full/` ou largeur >1000 px : classe HD ; quota public documenté | supportée, largeur prudente par défaut |
| PDF | `.pdf` | ARK / plage | PDF | quota public documenté : 4/min | supportée |
| Corpus / reprise | composition SDK | liste d'ARK | manifest + fichiers | doit respecter les quotas de toutes les primitives | 0.2 cible |

## Règle de statut

Une ligne ne doit pas être annoncée comme « supportée » dans la documentation publique du package uniquement parce que l'URL est connue. Pour une primitive réseau, il faut :

1. une construction de requête couverte par test ;
2. une réponse simulée couvrant le parsing ou la valeur retournée ;
3. un smoke test live depuis un réseau public ;
4. une documentation de la contrainte de quota lorsqu'elle existe.

## Choix d'interface Phase 1

- `Document.text()` expose `.texteBrut` au niveau document.
- `Page.text()` demande exactement une vue via `.texteBrut`.
- `Document.search_text()` expose `ContentSearch` sans inventer encore de modèle de résultat.
- `Gallica.periodical(ark).issue(date)` formalise uniquement la résolution datée déjà portée par `Issues`; le résultat est un `Document` normal.
- `Document.pdf()` permet le document entier ou une plage bornée de vues et utilise un bucket réseau séparé adapté au quota PDF.

## Sources de travail

Les contrats initiaux proviennent de la documentation publique api.bnf.fr et des validations réalisées dans `maribakulj/maj-scripts-api.bnf.fr`. Ce dépôt reste indépendant de son code : les connaissances sont reprises, pas son architecture ni ses adaptateurs legacy.

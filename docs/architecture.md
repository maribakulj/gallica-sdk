# Architecture

## Mission

`gallica-sdk` est une couche de référence programmable et vérifiée pour les services publics Gallica.

Le projet fournit deux artefacts liés :

1. un SDK Python léger pour notebooks, scripts et pipelines ;
2. une représentation machine-readable des capacités, services, contraintes et preuves opérationnelles afin qu'un agent puisse raisonner sur une base validée sans reconstruire l'API à chaque session.

Le projet ne crée pas une nouvelle API réseau. Le SDK appelle directement les services publics Gallica ; la référence programmable décrit ce que le projet a implémenté, observé et validé. La documentation et les services publics BnF restent l'autorité externe.

## Principes

1. Accès direct aux API publiques Gallica.
2. Pas de dépendance aux wrappers historiques PyGallica, Pyllica, Gallipy, gargallica ou bnfimage.
3. Pas d'abstraction sans cas d'usage démontré.
4. Pas d'effet de bord implicite : les méthodes retournent des valeurs ; l'écriture disque est explicite.
5. Objets Python simples, signatures typées et erreurs explicites.
6. Les primitives bas niveau restent accessibles lorsque l'abstraction de haut niveau ne suffit pas.
7. Les contraintes réseau et quotas sont centralisés dans le transport partagé.
8. Une opération réseau n'est dite supportée que lorsqu'elle dispose d'un test live public approprié.
9. La documentation doit être exploitable à la fois par un humain et par un agent qui génère du code.
10. La référence programmable, les signatures Python, les recettes agent et les preuves ne doivent pas dériver silencieusement les unes des autres.
11. Une preuve live est une observation datée, pas une garantie éternelle d'un service externe.
12. L'API publique doit rester petite et régulière.

## Architecture actuelle

```text
                      utilisateurs
            humain / notebook / pipeline / agent
                         |
              +----------+----------+
              |                     |
      référence programmable      SDK Python
        JSON / contrats          Gallica()
              |                     |
      services / preuves       +-----+---------+
              |                |     |         |
              |              Search Document  Corpus
              |                      |          |
              |                     Page    fichiers + manifest
              |                      |
              |              text / ALTO / image
              |                      |
              +----------+-----------+
                         |
                  transport HTTP
                         |
                services publics BnF
```

`Document`, `Page` et `Periodical` restent des façades minces. `Corpus` ajoute uniquement les comportements nécessaires aux traitements longs : reprise, écritures atomiques, manifest et isolation des erreurs par ARK.

La référence programmable est générée depuis la même source canonique que les contrats Python et relie les capacités aux services Gallica et aux preuves de validation.

## Surface fonctionnelle actuelle

Le SDK couvre notamment :

- recherche SRU et pagination paresseuse ;
- métadonnées OAIRecord ;
- pagination documentaire ;
- texte OCR et ContentSearch ;
- ALTO ;
- IIIF Image ;
- résolution datée de numéros de périodiques via Issues ;
- corpus reprenable pour métadonnées, texte, ALTO et images sur vues explicites.

La référence programmable expose en plus :

- index des capacités ;
- catalogue des services ;
- contraintes opérationnelles ;
- preuves live ;
- provenance des observations ;
- fraîcheur des preuves.

## Non-objectifs actuels

- serveur web ;
- MCP ;
- interface graphique ;
- framework de plugins ;
- compatibilité exhaustive avec les wrappers historiques ;
- cache distribué ;
- framework d'agents ;
- téléchargement implicite de toutes les vues ;
- multiplication d'adaptateurs qui dupliquent la logique métier.

Une CLI, une API async ou un MCP ne seront ajoutés que si un cas d'usage concret démontre qu'ils apportent une valeur supérieure à l'interface Python existante.

## Validation

La CI distingue :

- tests locaux sans réseau ;
- typage strict et lint ;
- construction et réinstallation du wheel ;
- smoke tests live contre Gallica public.

Le manifeste `reference/gallica-reference.json` doit correspondre exactement à sa représentation Python canonique. Les liens capacité → service → preuve doivent résoudre, et les preuves live enregistrent leur observation, commit et run CI.

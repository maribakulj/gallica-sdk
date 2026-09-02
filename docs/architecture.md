# Architecture

## Mission

`gallica-sdk` est une bibliothèque Python légère donnant un accès cohérent, typé et testable aux API publiques Gallica.

Elle ne crée pas une nouvelle API réseau. Elle appelle directement les services publics Gallica et normalise leurs contrats pour les développeurs, notebooks et outils automatisés.

## Principes

1. Accès direct aux API publiques Gallica.
2. Pas de dépendance aux wrappers historiques PyGallica, Pyllica, Gallipy, gargallica ou bnfimage.
3. Pas d'abstraction sans cas d'usage démontré.
4. Pas d'effet de bord implicite : les méthodes retournent des valeurs ; l'écriture disque est explicite.
5. Objets Python simples, signatures typées et erreurs explicites.
6. Les primitives bas niveau restent accessibles lorsque l'abstraction de haut niveau ne suffit pas.
7. Les contraintes réseau et quotas doivent être centralisés plutôt que réimplémentés par chaque méthode.
8. Une opération réseau n'est dite supportée que lorsqu'elle dispose de tests unitaires, d'intégration simulée et d'un smoke test live approprié.
9. La documentation doit être exploitable à la fois par un humain et par un agent qui génère du code.
10. L'API publique doit rester petite et régulière.

## Architecture cible initiale

```text
Utilisateur Python / notebook / agent
                |
             Gallica
        ________|________
       |        |        |
     Search  Document  (Corpus plus tard)
               |
              Page
               |
      text / alto / image
               |
           transport HTTP
               |
        API publiques Gallica
```

Les classes `Document` et `Page` sont des façades minces autour d'un ARK et d'un numéro de vue. Elles ne doivent pas devenir des conteneurs d'état complexes.

## Non-objectifs de la 0.1

- serveur web ;
- MCP ;
- interface graphique ;
- CLI complète ;
- framework de plugins ;
- compatibilité exhaustive avec les wrappers historiques ;
- cache distribué ;
- API async parallèle à l'API synchrone ;
- framework d'agents.

Ces éléments pourront être ajoutés uniquement lorsqu'un cas d'usage réel le justifie.

## Premier vertical slice

La première tranche fonctionnelle doit valider le modèle conceptuel avec :

- `Gallica.search()` ;
- `Gallica.document()` ;
- `Document.metadata()` ;
- `Document.page_count()` ;
- `Document.page()` ;
- `Page.alto()` ;
- `Page.iiif_info()` ;
- `Page.image()`.

Le reste est différé jusqu'à validation de cette interface contre Gallica réel.

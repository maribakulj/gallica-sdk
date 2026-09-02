# Utilisation par des agents

`gallica-sdk` n'embarque pas de modèle génératif et ne génère pas lui-même des scripts. Il expose une surface Python typée et un contrat machine-readable afin qu'un agent puisse comprendre les opérations supportées, leurs paramètres et leurs contraintes sans reconstruire les API Gallica à partir d'exemples fragiles.

## Point d'entrée machine-readable

```python
from gallica import Gallica

for capability in Gallica.capabilities():
    print(capability["id"], capability["call"])
```

Le même contrat peut être exporté en JSON :

```bash
python scripts/export_capabilities.py > capabilities.json
```

La source canonique est `src/gallica/agent.py`. Le script JSON n'entretient pas une seconde description indépendante.

Chaque capacité fournit :

- un identifiant stable ;
- l'appel Python correspondant ;
- une description ;
- le type retourné ;
- le service réseau concerné ;
- les paramètres ;
- les contraintes importantes.

Les capacités incluent aussi les constructeurs locaux `Gallica.document`, `Gallica.periodical` et `Gallica.corpus`, afin qu'un consommateur n'ait pas à deviner comment obtenir les objets sur lesquels les autres méthodes s'appliquent.

## Recettes

`agent/recipes.json` décrit des compositions courantes en référant uniquement aux identifiants de capacités canoniques. Les tests vérifient qu'aucune recette ne référence une capacité inexistante.

Exemples actuels :

- recherche SRU puis constitution d'un corpus de métadonnées ;
- récupération d'ALTO et d'images pour des vues explicites ;
- résolution d'un numéro de périodique puis accès à son OCR.

Une recette n'est pas un programme opaque. Elle indique un ordre d'opérations et les garde-fous à respecter ; l'agent produit ensuite le script Python adapté au besoin de l'utilisateur.

## Exemple de génération de script par un agent

Demande humaine :

```text
Pour ces ARK, récupère les métadonnées et le texte, reprends si le traitement a déjà commencé,
et produis un rapport des erreurs.
```

Le contrat permet à l'agent d'identifier `Gallica.corpus` et `Corpus.fetch`, puis de produire par exemple :

```python
from gallica import Gallica

arks = ["bpt6k5738219s", "bpt6k5460422k"]

with Gallica() as gallica:
    report = gallica.corpus(arks).fetch(
        "./corpus",
        metadata=True,
        text=True,
        resume=True,
    )

for failure in report.failures:
    print(failure.ark, failure.error)
```

La librairie n'a pas généré ce programme. Elle a fourni un vocabulaire et des contrats suffisamment explicites pour qu'un agent puisse le générer sans inventer des endpoints ou contourner les quotas.

## Règles importantes pour les agents

- utiliser les primitives du SDK lorsqu'elles existent plutôt que reconstruire les URLs Gallica ;
- utiliser `raw_xml` lorsqu'une information n'est pas encore modélisée ;
- conserver `maximum_records <= 50` pour SRU ;
- ne pas contourner le throttling `.texteBrut` ;
- utiliser 1000 px par défaut pour IIIF et considérer les largeurs supérieures comme HD ;
- fournir des vues explicites pour ALTO/images dans `Corpus` ;
- ne jamais interpréter une absence de vues comme « toutes les pages » ;
- considérer PDF comme non supporté tant qu'un contrat public reproductible n'est pas établi ;
- ne pas introduire de concurrence qui contourne le transport partagé.

## AGENTS.md

Le fichier racine `AGENTS.md` donne aux agents de développement les contraintes du dépôt : architecture, commandes de validation et règles de quotas. Il vise les environnements qui lisent automatiquement ce type de fichier, tout en restant compréhensible par un développeur humain.

## Pourquoi pas MCP maintenant ?

Le contrat machine-readable résout déjà le problème principal pour Claude Code, Codex ou un agent disposant de Python et d'un terminal : comprendre précisément quelles opérations sont disponibles et écrire du code dessus.

Un serveur MCP ajouterait un protocole et un processus supplémentaires. Il ne sera pertinent que si un cas d'usage exige réellement des appels d'outils directs sans environnement Python. La couche actuelle est conçue pour pouvoir servir de base à un MCP futur sans en dépendre.

## Anti-dérive

`tests/test_agent_contracts.py` vérifie notamment :

- l'unicité des identifiants ;
- la sérialisation JSON du contrat ;
- l'existence de chaque classe et méthode déclarée ;
- la présence de garde-fous essentiels ;
- la validité des identifiants référencés par les recettes.

Ainsi, la documentation machine-readable ne doit pas pouvoir annoncer tranquillement une méthode supprimée depuis trois versions, ce qui est malheureusement une fonctionnalité assez répandue de la documentation humaine.

# Utilisation par des agents

`gallica-sdk` n'embarque pas de modèle génératif et ne génère pas lui-même des scripts. Il expose une surface Python typée, une référence programmable et des preuves de validation afin qu'un agent puisse comprendre les opérations supportées, leurs paramètres, leurs contraintes et leur niveau d'observation sans reconstruire les API Gallica à partir d'exemples fragiles.

## Points d'entrée machine-readable

Pour découvrir le périmètre global sans installer le package, un agent peut lire :

```text
reference/gallica-reference.json
```

Ce manifeste indexe les services, les capacités, les preuves et leur provenance. Il est validé contre la représentation Python canonique.

Avec le package installé :

```python
from gallica import capabilities, evidence, evidence_freshness, programmable_reference

reference = programmable_reference()
contracts = capabilities()
proofs = evidence()
freshness = evidence_freshness()
```

Le contrat détaillé des capacités peut aussi être exporté en JSON :

```bash
python scripts/export_capabilities.py > capabilities.json
```

La référence de découverte peut être régénérée avec :

```bash
python scripts/export_reference.py
```

Les sources canoniques sont dans `src/gallica/agent.py`, `src/gallica/reference.py` et `src/gallica/evidence.py`. Les fichiers JSON publiés ne constituent pas une seconde description indépendante.

Chaque capacité fournit notamment :

- un identifiant stable ;
- l'appel Python correspondant ;
- une description ;
- le type retourné ;
- les paramètres ;
- les contraintes importantes.

Le graphe de référence relie ensuite chaque capacité réseau aux services Gallica et aux preuves live pertinentes. Une preuve live enregistre son test cible, sa date d'observation, le commit testé, le run CI et une fenêtre de fraîcheur.

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

## Interpréter les preuves

`passing-in-ci` signifie qu'un test live a réussi lors de l'observation enregistrée. Ce statut n'est pas une garantie perpétuelle du service externe.

Un agent peut utiliser :

```python
from gallica import evidence_freshness

for item in evidence_freshness():
    print(item["id"], item["state"], item["age_days"])
```

Une preuve `stale` reste une observation historique valide, mais elle doit normalement conduire l'agent à revalider le comportement avant de s'appuyer fortement sur un service externe susceptible d'avoir changé.

## Règles importantes pour les agents

- utiliser les primitives du SDK lorsqu'elles existent plutôt que reconstruire les URLs Gallica ;
- consulter la référence programmable pour distinguer supporté, non supporté et fraîcheur des preuves ;
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

La référence programmable et le contrat machine-readable résolvent déjà le problème principal pour Claude Code, Codex ou un agent disposant de Python et d'un terminal : comprendre précisément quelles opérations sont disponibles et écrire du code dessus.

Un serveur MCP ajouterait un protocole et un processus supplémentaires. Il ne sera pertinent que si un cas d'usage exige réellement des appels d'outils directs sans environnement Python. La couche actuelle est conçue pour pouvoir servir de base à un MCP futur sans en dépendre.

## Anti-dérive

Les tests vérifient notamment :

- l'unicité des identifiants ;
- la sérialisation JSON des contrats ;
- l'existence de chaque classe et méthode déclarée ;
- la présence de garde-fous essentiels ;
- la validité des identifiants référencés par les recettes ;
- la résolution des liens capacité → service → preuve ;
- l'égalité entre le manifeste JSON publié et la représentation Python canonique ;
- la cohérence des versions de package, README et schéma de référence.

Ainsi, la documentation machine-readable ne doit pas pouvoir annoncer tranquillement une méthode supprimée depuis trois versions, ce qui est malheureusement une fonctionnalité assez répandue de la documentation humaine.

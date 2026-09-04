# Utilisation par des agents

`gallica-sdk` n'embarque pas de modèle génératif et ne génère pas lui-même des scripts. Il expose une surface Python typée, une référence programmable et des preuves de validation afin qu'un agent puisse comprendre les opérations supportées sans reconstruire les API Gallica à partir d'exemples fragiles.

## Trois niveaux de découverte

### 1. Référence de découverte

Sans installer le package, lire :

```text
reference/gallica-reference.json
```

Ce manifeste versionné indexe services, capacités, preuves, provenance et commandes d'export. Il reste volontairement compact.

### 2. Contrat minimal de signature

Avec le package installé :

```python
from gallica import capabilities

for capability in capabilities():
    print(capability["id"], capability["call"], capability["parameters"])
```

`capabilities()` est approprié lorsqu'un agent a surtout besoin de savoir quelles méthodes existent, quels paramètres elles acceptent et quelles contraintes immédiates s'appliquent.

### 3. Contrat opérationnel résolu

Lorsqu'un agent doit décider comment exécuter une opération et évaluer son niveau de confiance :

```python
from gallica import operational_contract

contract = operational_contract("page_alto")
print(contract["parameters"])
print(contract["services"])
print(contract["output_semantics"])
print(contract["errors"])
print(contract["evidence"])
print(contract["freshness"])
```

Le contrat résolu contient :

- l'identifiant stable et l'appel Python ;
- les paramètres et contraintes ;
- le type retourné ;
- le media type source lorsqu'il est pertinent ;
- la sémantique de sortie ;
- les erreurs attendues ;
- les services Gallica concernés ;
- les preuves live liées ;
- leur fraîcheur ;
- l'exemple associé lorsqu'il existe.

Il est construit à partir des contrats, services et preuves canoniques existants. Ce n'est pas une copie indépendante destinée à dériver discrètement six mois plus tard.

Tous les contrats résolus sont exportables :

```bash
python scripts/export_capabilities.py > capabilities.json
python scripts/export_operational_contracts.py > operational-contracts.json
python scripts/export_reference.py > reference.json
```

## Recettes

`agent/recipes.json` décrit des compositions courantes en référant uniquement aux identifiants de capacités canoniques. Les tests vérifient qu'aucune recette ne référence une capacité inexistante.

Exemples actuels :

- recherche SRU puis constitution d'un corpus de métadonnées ;
- récupération d'ALTO et d'images pour des vues explicites ;
- résolution d'un numéro de périodique puis accès à son OCR.

Une recette n'est pas un programme opaque. Elle indique un ordre d'opérations et les garde-fous à respecter ; l'agent produit ensuite le script Python adapté au besoin de l'utilisateur.

## Exemple de génération de script

Demande humaine :

```text
Pour ces ARK, récupère les métadonnées et le texte, reprends si le traitement a déjà commencé,
et produis un rapport des erreurs.
```

Un agent peut d'abord inspecter :

```python
from gallica import operational_contract

print(operational_contract("corpus"))
print(operational_contract("corpus_fetch"))
```

puis produire :

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

La librairie n'a pas généré le programme. Elle fournit un vocabulaire, des contrats et des preuves suffisamment explicites pour que l'agent n'ait pas à inventer des endpoints ou contourner les quotas.

## Interpréter les preuves

`passing-in-ci` signifie qu'un test live a réussi lors de l'observation enregistrée. Ce statut n'est pas une garantie perpétuelle du service externe.

```python
from gallica import evidence_freshness

for item in evidence_freshness():
    print(item["id"], item["state"], item["age_days"])
```

Une preuve `stale` reste une observation historique valide, mais elle doit normalement conduire l'agent à revalider le comportement avant de s'appuyer fortement sur un service susceptible d'avoir changé.

## Règles importantes

- utiliser les primitives du SDK lorsqu'elles existent plutôt que reconstruire les URLs Gallica ;
- utiliser `operational_contract()` lorsqu'il faut connaître erreurs, services et preuves en plus de la signature ;
- utiliser `raw_xml` lorsqu'une information n'est pas encore modélisée ;
- conserver `maximum_records <= 50` pour SRU ;
- ne pas contourner le throttling `.texteBrut` ;
- utiliser 1000 px par défaut pour IIIF et considérer les largeurs supérieures comme HD ;
- fournir des vues explicites pour ALTO/images dans `Corpus` ;
- ne jamais interpréter une absence de vues comme « toutes les pages » ;
- considérer PDF comme non supporté tant qu'un contrat public reproductible n'est pas établi ;
- ne pas introduire de concurrence qui contourne le transport partagé.

## Pourquoi pas MCP maintenant ?

La référence programmable, les contrats résolus et l'API Python couvrent déjà le besoin principal pour Claude Code, Codex ou un agent disposant de Python et d'un terminal. Un MCP ajouterait un protocole et un processus supplémentaires sans supprimer la nécessité de maintenir les contrats sous-jacents.

## Anti-dérive

Les tests vérifient notamment :

- l'unicité des identifiants ;
- la sérialisation JSON ;
- l'existence des méthodes déclarées ;
- la validité des recettes ;
- la résolution capacité → service → preuve ;
- la présence d'une sémantique de sortie et d'erreurs pour chaque contrat opérationnel ;
- la présence de preuves live pour les contrats réseau ;
- l'égalité entre le manifeste JSON publié et sa représentation Python canonique ;
- la cohérence des versions de package, README et schéma de référence.

Ainsi, la documentation machine-readable ne doit pas pouvoir annoncer tranquillement une méthode supprimée depuis trois versions, sport documentaire qui avait déjà suffisamment d'adeptes avant l'arrivée des agents.

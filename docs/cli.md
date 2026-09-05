# CLI

`gallica-sdk` fournit une CLI volontairement mince au-dessus du même SDK Python. Elle n'implémente aucun endpoint, retry ou règle de quota séparément.

Après installation :

```bash
gallica --help
```

Les sorties sont JSON compactes par défaut. `--pretty` active une mise en forme lisible.

## Référence et capacités

```bash
gallica reference
gallica capabilities
gallica contract page_alto
```

Ces commandes n'effectuent pas de requête réseau. Elles exposent les mêmes structures que `programmable_reference()`, `capabilities()` et `operational_contract()`.

## Recherche

```bash
gallica search 'gallica all "Verdun"' --limit 10
```

`--limit` est limité à 1..50 comme `Gallica.search()`. `--start-record` permet de demander une page SRU explicite.

La sortie contient la requête, le nombre total annoncé par SRU et les notices de la page courante avec tous leurs champs Dublin Core répétables.

## Métadonnées

```bash
gallica metadata bpt6k5738219s
```

La sortie contient l'ARK, les champs techniques modélisés et la notice Dublin Core structurée. Le XML brut reste disponible via l'API Python lorsqu'il est nécessaire ; la CLI ne duplique pas systématiquement les réponses XML dans son JSON.

## Nombre de vues

```bash
gallica page-count bpt6k5738219s
```

La sortie est de la forme :

```json
{"ark":"bpt6k5738219s","page_count":374}
```

## Pourquoi une CLI limitée ?

La CLI vise l'inspection et quelques opérations sûres qui se sérialisent naturellement en JSON. Les téléchargements binaires, les corpus volumineux et les workflows complexes restent plus explicites avec l'API Python. Une commande CLI ne doit être ajoutée que si elle reste une enveloppe mince autour d'une primitive publique déjà testée.

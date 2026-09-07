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

## Facettes Categories

```bash
gallica categories 'gallica all "Verdun"'
```

La commande appelle directement `Gallica.categories()`. Elle expose les catégories rencontrées et chaque valeur typée avec `clean_value`, label éventuel, compte `howMany` explicitement approximatif et champ CQL associé lorsqu'il est connu.

Comme dans l'API Python, une réponse HTML/403 amont n'est jamais convertie en pseudo-résultat Categories. Le service reste `environment-limited` depuis certains environnements publics.

## Métadonnées

```bash
gallica metadata bpt6k5738219s
```

La sortie contient l'ARK, les champs techniques modélisés et la notice Dublin Core structurée. Le XML brut reste disponible via l'API Python lorsqu'il est nécessaire ; la CLI ne duplique pas systématiquement les réponses XML dans son JSON.

## Structure du document

Pour le simple nombre de vues :

```bash
gallica page-count bpt6k5738219s
```

La sortie est de la forme :

```json
{"ark":"bpt6k5738219s","page_count":374}
```

Pour la structure Pagination complète :

```bash
gallica pagination bpt6k5738219s --pretty
```

La sortie reprend le modèle `Pagination` : compte de vues image/audio, drapeaux de navigation, emplacement éventuel du sommaire et pages logiques avec ordre, numéro, type et légende.

Pour la table des matières :

```bash
gallica toc bpt6k97540464 --pretty
```

`toc` conserve la représentation amont dans le champ `raw`, parce que le contenu HTML ou TEI est précisément la ressource demandée. `format` et `well_formed` permettent de distinguer les formes historiques sans les normaliser de force.

## IIIF Presentation

```bash
gallica iiif-manifest btv1b550076223 --pretty
```

La commande délègue à `Document.iiif_manifest()` et expose la version détectée, l'identifiant, les contextes et le nombre de canvases. Le manifeste JSON complet peut être volumineux ; il reste disponible comme `manifest.raw_json` dans l'API Python au lieu d'être recopié dans chaque sortie CLI.

## IIIF Image info.json

```bash
gallica iiif-info btv1b53066668g 1 --pretty
```

Le second argument est le numéro de vue, strictement positif. La sortie reprend `IIIFImageInfo` : version détectée (`2`, `3` ou `unknown`), identifiant, contextes, protocole, profils annoncés et dimensions.

Le JSON amont exact reste disponible avec `Page.iiif_info().raw_json` côté Python. Sur le document actuellement utilisé par la validation live, Gallica fournit des dimensions valides sans marqueur v2/v3 exploitable par ce contrat ; la version reste donc honnêtement `unknown` au lieu d'être déduite d'une documentation externe.

## Pourquoi une CLI limitée ?

La CLI vise l'inspection et quelques opérations sûres qui se sérialisent naturellement en JSON. Les téléchargements binaires, les corpus volumineux et les workflows complexes restent plus explicites avec l'API Python. Une commande CLI ne doit être ajoutée que si elle reste une enveloppe mince autour d'une primitive publique déjà testée.

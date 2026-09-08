# Public API boundary for 0.2

This page records the pre-release API audit for the first public `0.2.x` line. Its purpose is not to make the SDK impossible to evolve. It makes compatibility decisions explicit before a stable release turns today's accidents into tomorrow's obligations.

## What counts as public

The package-level compatibility boundary is `gallica.__all__` plus the documented methods and fields of the objects exported there.

Importable implementation helpers that are not exported from `gallica` are not part of that compatibility promise. Examples include transport internals, parsers, live-evidence recording helpers and private `_...` client methods. They may move as the implementation evolves.

The machine-readable `capabilities()` contract is narrower than the whole Python public API: it describes operational user actions, not every result model, helper property or evidence type.

## Audit result

No core user-facing method needs to be removed or renamed before `0.2.0`.

### Core handles: KEEP

- `Gallica`
- `Document`
- `Page`
- `Periodical`
- `Corpus`

`Gallica` remains synchronous and context-manager friendly. `Document` and `Page` remain lightweight handles whose network work happens only when an access method is called. `Periodical.issue()` continues to resolve an exact date to `Document | None`. `Corpus.fetch()` keeps explicit page views for ALTO/images and does not gain an implicit all-pages mode before the first release.

`Document.page_count()` is intentionally retained even though it projects `Document.pagination().image_views`. It is a useful convenience method, while Pagination remains the single parsing contract underneath it.

### Search and document result models: KEEP

- `DublinCoreRecord`
- `SearchResults`
- `CategoryValue`
- `Categories`
- `DocumentMetadata`
- `PaginationPage`
- `Pagination`
- `TocDocument`
- `ContentSearchMatch`
- `ContentSearchItem`
- `ContentSearchResults`
- `IIIFPresentationManifest`
- `IIIFImageInfo`

The field names of these dataclasses are part of the audited 0.2 surface and are checked in CI.

`ContentSearchItem.alto_id` is retained as a compatibility convenience. It is not a second geometry model: when geometric matches exist, it points to the first `ContentSearchMatch.alto_id`; otherwise it preserves the historical direct `<altoid>` value. Consumers needing coordinates or multiple occurrences should use `item.matches`.

### Raw upstream payload naming: KEEP

The apparent naming difference is intentional rather than accidental:

- XML-backed structured models use `raw_xml`;
- JSON-backed structured models use `raw_json`;
- `TocDocument` uses `raw` because the upstream representation may be either HTML or TEI XML.

The SDK does not rename `TocDocument.raw` to `raw_xml` because that would incorrectly describe legacy HTML payloads.

### Corpus result models: KEEP

- `CorpusArtifactRecord`
- `CorpusArtifactFailure`
- `CorpusItemResult`
- `CorpusReport`

These types are public because resumability and failure provenance are part of the corpus contract, not merely logging details. `CorpusItemResult.failure_details`, `CorpusItemResult.retryable` and `CorpusReport.retryable` remain supported inspection points.

### Errors: KEEP

- `GallicaError`
- `GallicaResponseError`

`GallicaResponseError` represents an upstream payload that reached the SDK as an HTTP success but violates the expected service contract. Argument validation continues to use `ValueError`. Transport and HTTP failures that originate in `httpx` are not wrapped merely to create a larger exception hierarchy; their original information remains available to callers.

### Programmable reference and evidence API: KEEP

The following exports remain public because the project explicitly serves agents and automated consumers as well as direct Python users:

- `CapabilitySpec`, `capabilities()` and `Gallica.capabilities()`;
- `ReferenceSpec` and `programmable_reference()`;
- `OperationalContract`, `operational_contract()` and `operational_contracts()`;
- `EvidenceSpec`, `CapabilityEvidence`, `EvidenceAttestation`, `EvidenceAttestationRecord`, `EvidenceFreshness`;
- `evidence()`, `capability_evidence()`, `build_evidence_attestation()`, `load_evidence_attestation()` and `evidence_freshness()`.

Low-level CI collection helpers such as `record_live_evidence()` are deliberately not re-exported from the package root. They remain implementation tooling rather than a general user contract.

### Constants and version: KEEP

- `CATEGORY_CQL_FIELDS` remains public because the documented Categories → CQL mapping is useful independently of a single `CategoryValue` instance. Unknown mappings must still produce `None` through `CategoryValue.cql_field`; the table is not permission to guess undocumented mappings.
- `__version__` remains the installed package version and the HTTP User-Agent version source.

## Signature decisions

The following choices are deliberately frozen for the first 0.2 release line:

- query pagination controls stay keyword-only;
- `Page.image(width=1000, fmt="jpg")` keeps image options keyword-only;
- `Corpus.fetch()` keeps artifact switches, views, image width and resume behavior keyword-only;
- views and page numbers remain 1-based;
- no public async twin is introduced before release;
- no implicit generalized concurrency or all-pages download mode is introduced before release.

CI checks the parameter names, positional/keyword boundary and defaults of the main user-facing methods so an accidental signature drift fails before merge.

## What is not frozen

The audit does not promise compatibility for:

- private names beginning with `_`;
- non-root-exported parsing, transport and live-test helpers;
- exact internal request construction beyond the documented operational contract;
- undocumented fields present only inside `raw_xml` / `raw_json` payloads;
- CLI formatting whitespace; the CLI contract is JSON data, not byte-for-byte presentation;
- future additive fields or helpers when they can be introduced compatibly.

## Change policy after 0.2.0

A deliberate public API change is still possible. It should update the public-surface test, this audit page or its successor, the changelog and any affected capability/operational contracts in the same pull request.

The test is therefore a tripwire, not constitutional law. Humans remain allowed to change software, regrettably, but they have to leave evidence that they meant to do it.

# Changelog

All notable changes to `gallica-sdk` will be documented in this file.

The project follows semantic versioning for public release candidates and releases.

## Unreleased

No changes yet since `0.2.0rc1`.

## 0.2.0rc1 - 2026-09-08

### Added

- typed Python access to Gallica SRU, Categories, OAIRecord, Pagination, Toc, Issues, ContentSearch, plain OCR text, ALTO, IIIF Image and IIIF Presentation services;
- `Gallica.categories()` with typed search refinements, approximate-count semantics, official Categories → CQL field mapping and raw JSON preservation;
- structured `Document.pagination()` access with navigation metadata, image/audio view counts and logical page labels while preserving raw XML;
- `Document.toc()` with explicit preservation of legacy HTML versus TEI XML table-of-contents representations;
- `Document.iiif_manifest()` with explicit IIIF Presentation v2/v3 detection, version-specific validation, canvas counts and raw JSON preservation without lossy v2→v3 normalization;
- typed `IIIFImageInfo` returned by `Page.iiif_info()`, with explicit Image API version detection, identifier, contexts, protocol, advertised profile URIs, positive dimensions and raw JSON preservation;
- `Document`, `Page`, `Periodical` and resumable `Corpus` abstractions;
- lazy SRU pagination and search-result handoff to corpus workflows;
- JSONL export for search results;
- resumable corpus downloads with atomic writes, manifest tracking and per-artifact failure isolation;
- machine-readable capability contracts and agent recipes;
- programmable Gallica service reference with JSON Schema;
- capability → service → evidence graph;
- run-specific JSONL live observations with explicit `operational` versus `environment-limited` service outcomes;
- live-validation provenance, observation timestamps and evidence freshness classification;
- resolved operational contracts combining signature, output semantics, expected errors, services, evidence and freshness;
- `operational_contract()` and `operational_contracts()` plus JSON export support;
- JSON-first `gallica` CLI for reference/capability inspection, SRU search, Categories, metadata, Pagination, Toc and typed IIIF Presentation/Image inspection;
- PEP 561 `py.typed` marker for downstream type checkers;
- user guides for search, documents/pages, periodicals, corpus, quotas, errors and CLI usage;
- generated canonical capability sections in `README.md` and `docs/capabilities.md` with a CI anti-drift check;
- explicit `docs/public-api.md` audit of the intended 0.2 release boundary;
- deterministic public-API lock tests for root exports, facade call signatures and public result-model fields;
- Apache License 2.0 repository and PEP 639 package metadata;
- distribution validation requiring Apache-2.0 metadata and the license file in both wheel and sdist;
- executable notebooks for search/metadata, resumable corpus workflows, and document structure/IIIF inspection;
- CI execution of the reference notebooks against public Gallica services;
- release metadata/tag validator;
- release-candidate workflow that builds and retains validated wheel/sdist artifacts;
- guarded TestPyPI Trusted Publishing boundary that consumes the exact validated release-candidate artifacts in a separate OIDC-only job;
- isolated wheel and sdist installation checks with `pip check`;
- installed CLI smoke checks from both wheel and sdist;
- installed `py.typed` verification from both wheel and sdist;
- `twine check` validation for built distributions;
- CI for Python 3.11 through 3.14, Ruff, mypy strict, coverage, wheel/sdist packaging, Windows/macOS smoke tests and public Gallica smoke tests.

### Changed

- the package version advanced from `0.2.0.dev0` to the first release candidate, `0.2.0rc1`;
- release-candidate validation now rejects development versions when run manually;
- TestPyPI publication is isolated from build machinery, requires GitHub OIDC, a `testpypi` environment, the repository variable `TESTPYPI_PUBLISH_ENABLED=true`, an explicit manual publish input and execution from `main`;
- CI evidence attestations now require one observation for every declared live test and use schema 2.0 with separate test and service outcomes; legacy schema-1.0 attestations remain readable without being promoted to operational evidence;
- live evidence declarations no longer embed historical timestamps, commits or workflow runs; run-specific provenance exists only in generated attestations;
- human capability documentation is now projected from the canonical capability/service graph instead of maintaining a second hand-written API inventory;
- the first-release public Python surface has been audited and deliberately frozen before 0.2.0 rather than being treated as an accidental consequence of imports;
- release validation now treats license agreement between source metadata, wheel and sdist as a hard requirement;
- `Document.page_count()` is now a projection of the structured `Pagination.image_views` contract rather than a separate XML parsing path;
- project positioning expanded from a Python-only SDK to a verified programmable reference plus Python SDK;
- package version is exposed as `gallica.__version__` and used in the HTTP `User-Agent`;
- programmable reference schema advanced to 2.0 to advertise the operational-contract export;
- README is a navigable entry point to task-focused documentation rather than the only user guide;
- package CI validates both wheel and source-distribution installation paths.

### Known limitations

- automated PDF access is intentionally unsupported until a reproducible public contract is validated;
- IIIF Presentation public machine access is currently environment-limited from some cold external runners even though the BnF documents the v2 manifest endpoint;
- page-level corpus downloads require explicit views and never imply all pages;
- no MCP, async public API, Parquet/DataFrame export or implicit high-volume concurrency is provided yet;
- `main` still lacks enforced branch protection/rulesets;
- TestPyPI Trusted Publishing must still be configured externally and the guarded publication path must be exercised successfully before the final release;
- production PyPI publication remains intentionally disabled until the final release boundary is configured.

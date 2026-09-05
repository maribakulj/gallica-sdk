# Changelog

All notable changes to `gallica-sdk` will be documented in this file.

The project follows semantic versioning once a first public release is published. Until then, `0.2.0.dev0` remains a development version and may change before the first tagged release.

## Unreleased

### Added

- typed Python access to Gallica SRU, OAIRecord, Pagination, Issues, ContentSearch, plain OCR text, ALTO and IIIF Image services;
- `Document`, `Page`, `Periodical` and resumable `Corpus` abstractions;
- lazy SRU pagination and search-result handoff to corpus workflows;
- JSONL export for search results;
- resumable corpus downloads with atomic writes, manifest tracking and per-ARK failure isolation;
- machine-readable capability contracts and agent recipes;
- programmable Gallica service reference with JSON Schema;
- capability → service → evidence graph;
- live-validation provenance, observation timestamps and evidence freshness classification;
- resolved operational contracts combining signature, output semantics, expected errors, services, evidence and freshness;
- `operational_contract()` and `operational_contracts()` plus JSON export support;
- JSON-first `gallica` CLI for reference/capability inspection, SRU search, metadata and page counts;
- PEP 561 `py.typed` marker for downstream type checkers;
- user guides for search, documents/pages, periodicals, corpus, quotas, errors and CLI usage;
- executable notebooks for search/metadata and resumable corpus workflows;
- CI execution of the reference notebooks against public Gallica services;
- release metadata/tag validator;
- non-publishing release-candidate workflow that validates and retains wheel/sdist artifacts;
- isolated wheel and sdist installation checks with `pip check`;
- installed CLI smoke checks from both wheel and sdist;
- installed `py.typed` verification from both wheel and sdist;
- `twine check` validation for built distributions;
- CI for Python 3.11 and 3.12, Ruff, mypy strict, wheel/sdist packaging and public Gallica smoke tests.

### Changed

- project positioning expanded from a Python-only SDK to a verified programmable reference plus Python SDK;
- package version is now exposed as `gallica.__version__` and used in the HTTP `User-Agent`;
- programmable reference schema advanced to 2.0 to advertise the operational-contract export;
- README is now a navigable entry point to task-focused documentation rather than the only user guide;
- package CI now validates both wheel and source-distribution installation paths.

### Known limitations

- automated PDF access is intentionally unsupported until a reproducible public contract is validated;
- page-level corpus downloads require explicit views and never imply all pages;
- no MCP, async public API, Parquet/DataFrame export or implicit high-volume concurrency is provided yet;
- PyPI publication remains intentionally disabled until license, version policy and publishing trust configuration are decided.

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
- CI for Python 3.11 and 3.12, Ruff, mypy strict, wheel/sdist packaging and public Gallica smoke tests.

### Changed

- project positioning expanded from a Python-only SDK to a verified programmable reference plus Python SDK;
- package version is now exposed as `gallica.__version__` and used in the HTTP `User-Agent`.

### Known limitations

- automated PDF access is intentionally unsupported until a reproducible public contract is validated;
- page-level corpus downloads require explicit views and never imply all pages;
- no CLI, MCP, async public API, Parquet/DataFrame export or implicit high-volume concurrency is provided yet.

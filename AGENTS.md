# Agent instructions

This repository is a thin Python SDK over the public Gallica APIs. Do not invent additional network layers, undocumented endpoints, or wrapper-specific behavior.

## Preferred workflow

1. Inspect `Gallica.capabilities()` or run `python scripts/export_capabilities.py` for the machine-readable supported surface.
2. Read `agent/recipes.json` for common compositions.
3. Use the typed Python API rather than reconstructing Gallica URLs manually when a supported primitive already exists.
4. Keep `raw_xml` when an advanced use case needs data not yet promoted into typed models.
5. For corpus work, use `Corpus.fetch(..., resume=True)` rather than writing an independent downloader unless the SDK genuinely lacks the required primitive.

## Safety and quota rules

- SRU `maximum_records` must be between 1 and 50.
- `.texteBrut` is throttled by the SDK; do not bypass the shared transport.
- IIIF images default to 1000 px. Widths above 1000 px use the HD rate bucket.
- Corpus ALTO/images require explicit `views`.
- Never reinterpret a missing `views` argument as “all pages”.
- PDF is not a supported SDK capability. Historical `.pdf` forms returned HTML in public automated validation on 2026-09-02.
- Do not add concurrency that bypasses transport throttling.

## Architecture constraints

Keep the dependency direction simple:

```text
user / notebook / agent
        ↓
      Gallica
        ↓
Document / Page / Periodical / Corpus
        ↓
     Transport
        ↓
 public Gallica APIs
```

Avoid service/repository/factory layers unless a concrete case proves they reduce complexity.

## Validation requirement

A network primitive is not considered supported merely because its URL is known. It requires deterministic tests and a public live smoke test. Corpus features additionally require resume and partial-artifact tests.

Run before proposing a change:

```bash
ruff check src tests
mypy src/gallica
pytest -m 'not live'
pytest -m live tests/test_live.py
```

Live tests intentionally exercise the public service and should not be multiplied casually.

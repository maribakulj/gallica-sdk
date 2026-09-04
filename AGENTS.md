# Agent instructions

This repository is a verified programmable reference and thin Python SDK over the public Gallica services. Do not invent additional network layers, undocumented endpoints, or wrapper-specific behavior.

## Preferred workflow

1. Inspect `reference/gallica-reference.json` or `programmable_reference()` for the validated service/capability/evidence graph.
2. Inspect `Gallica.capabilities()` or run `python scripts/export_capabilities.py` for detailed machine-readable signatures and constraints.
3. Read `agent/recipes.json` for common compositions.
4. Use the typed Python API rather than reconstructing Gallica URLs manually when a supported primitive already exists.
5. Check `evidence_freshness()` when relying on volatile external behavior.
6. Keep `raw_xml` when an advanced use case needs data not yet promoted into typed models.
7. For corpus work, use `Corpus.fetch(..., resume=True)` rather than writing an independent downloader unless the SDK genuinely lacks the required primitive.

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
reference JSON / humans / notebooks / agents
                  |
               Gallica
          ________|________
         |        |        |
      Search   Document   Corpus
                  |
                 Page
                  |
              Transport
                  |
        public Gallica services
```

The programmable reference describes the same capabilities; it is not a second implementation layer.

Avoid service/repository/factory layers unless a concrete case proves they reduce complexity.

## Validation requirement

A network primitive is not considered supported merely because its URL is known. It requires deterministic tests and a public live smoke test. Corpus features additionally require resume and partial-artifact tests.

Reference changes must preserve the capability → service → evidence graph and the equality between the checked-in JSON manifest and its canonical Python representation.

Run before proposing a change:

```bash
ruff check src tests
mypy src/gallica
pytest -m 'not live'
pytest -m live tests/test_live.py tests/test_live_usability.py
```

Live tests intentionally exercise the public service and should not be multiplied casually.

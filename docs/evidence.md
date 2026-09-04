# Validation evidence and provenance

`gallica-sdk` distinguishes implementation from evidence. A capability may exist in Python, but network-facing behavior is only treated as supported when the programmable reference links it to a relevant public live test.

The canonical graph is available through:

```python
from gallica import programmable_reference

reference = programmable_reference()
```

and in the checked-in `reference/gallica-reference.json` file for consumers that do not install the Python package.

## Evidence model

Each evidence item has a stable ID, a kind, a status and a repository target. Current kinds are:

- `live-test`: a test that calls public Gallica services from CI;
- `example`: a checked-in workflow intended for humans and coding agents.

`passing-in-ci` means the referenced live test passes in the maintained GitHub Actions workflow at the current revision. It is operational evidence, not a promise that an external BnF service can never change.

## Capability links

Every public capability has exactly one `capability_evidence` record. It identifies:

- the Gallica service IDs involved;
- the evidence IDs that validate the behavior;
- an optional minimal example.

For example, an agent can inspect `page_alto`, see that it depends on the `alto` service, and resolve the linked evidence to `tests/test_live.py::test_public_gallica_vertical_slice` and `tests/test_live.py::test_public_gallica_corpus_page_artifacts`.

Local handle constructors such as `Gallica.document()` do not require a public network test because they make no network request themselves.

## Authority

This evidence graph describes what `gallica-sdk` has implemented and observed. BnF documentation and the public Gallica services remain authoritative. When documentation, implementation and live behavior disagree, the discrepancy should be recorded rather than hidden behind an abstraction.

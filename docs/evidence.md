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

A live observation also records `observed_at`, the exact tested commit, the GitHub Actions run, a freshness window and a confidence label. These fields describe a historical observation. They are not silently rewritten when time passes.

`passing-in-ci` therefore means: the referenced live test passed in the recorded CI observation. It is operational evidence, not a promise that an external BnF service can never change.

## Freshness

Consumers that install the package can ask for an interpretation relative to the current date or to a reproducible date supplied explicitly:

```python
from datetime import date
from gallica import evidence_freshness

for item in evidence_freshness(as_of=date(2026, 9, 10)):
    print(item["id"], item["state"], item["age_days"])
```

Possible states are `fresh`, `stale`, `unknown` and `not-applicable`. Freshness does not erase or rewrite the underlying evidence. A stale successful observation remains a successful historical observation, but an agent should normally revalidate it before relying on volatile external behavior.

The default freshness window for the current live tests is 14 days. This is a maintenance policy of this project, not a BnF guarantee.

## Capability links

Every public capability has exactly one `capability_evidence` record. It identifies the Gallica service IDs involved, the evidence IDs that validate the behavior, and an optional minimal example.

For example, an agent can inspect `page_alto`, see that it depends on the `alto` service, and resolve the linked evidence to `tests/test_live.py::test_public_gallica_vertical_slice` and `tests/test_live.py::test_public_gallica_corpus_page_artifacts`.

Local handle constructors such as `Gallica.document()` do not require a public network test because they make no network request themselves.

## Authority

This evidence graph describes what `gallica-sdk` has implemented and observed. BnF documentation and the public Gallica services remain authoritative. When documentation, implementation and live behavior disagree, the discrepancy should be recorded rather than hidden behind an abstraction.

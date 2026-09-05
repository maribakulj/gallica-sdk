# Validation evidence and provenance

`gallica-sdk` distinguishes three things that are easy to confuse: implementation, evidence declaration and validation attestation.

A capability may exist in Python. The programmable reference then links network-facing behavior to a stable live-test evidence ID. A successful CI run can finally emit an attestation saying that those declared tests actually passed for one exact commit and one exact GitHub Actions run.

The declaration graph is available through:

```python
from gallica import programmable_reference

reference = programmable_reference()
```

and in the checked-in `reference/gallica-reference.json` file.

## Evidence declarations

Each evidence item has a stable ID, a kind, a status and a repository target. Current kinds are:

- `live-test`: a test that calls public Gallica services;
- `example`: a checked-in workflow intended for humans and coding agents.

The historical `observed_at`, commit and run fields still present in schema 2.0 describe an older recorded observation and are retained for compatibility. They are no longer treated as the current validation state by `evidence_freshness()`.

This distinction matters because a checked-in Python constant cannot magically become newer when CI runs. Humans have attempted similar tricks with timestamps for decades; clocks remain unimpressed.

## CI attestations

After the complete live suite passes, CI runs:

```bash
python scripts/generate_evidence_attestation.py
```

and uploads `evidence-attestation.json` as a GitHub Actions artifact. The attestation contains:

- the exact commit SHA;
- the exact Actions run URL;
- generation/observation timestamp;
- one `passed` record for every declared `live-test` evidence ID;
- the confidence label associated with the declaration.

No attestation is generated when the live-test step fails.

The normal CI live job emits such an artifact for validated PR/push runs. A dedicated `Live evidence` workflow also runs every Sunday and can be started manually, so external service changes can be detected even when nobody commits code.

## Freshness

Without an explicit current attestation, live freshness is intentionally `unknown`:

```python
from gallica import evidence_freshness

assert evidence_freshness()[0]["state"] == "unknown"
```

A downloaded attestation can be loaded and supplied explicitly:

```python
from datetime import date
from gallica import evidence_freshness, load_evidence_attestation

attestation = load_evidence_attestation("evidence-attestation.json")
for item in evidence_freshness(attestation=attestation, as_of=date(2026, 9, 10)):
    print(item["id"], item["state"], item["age_days"])
```

Possible states are `fresh`, `stale`, `failed`, `unknown` and `not-applicable`. A successful attestation becomes stale after the declaration's freshness window, currently 14 days for the live tests. That window is project policy, not a BnF guarantee.

Operational contracts accept the same attestation:

```python
from gallica import operational_contract

contract = operational_contract("page_alto", attestation=attestation)
```

Without it, the contract still knows its services and evidence targets, but reports live freshness as `unknown` rather than pretending a historical snapshot is current.

## Capability links

Every public capability has exactly one `capability_evidence` record. It identifies the Gallica service IDs involved, the evidence IDs that validate the behavior, and an optional minimal example.

For example, an agent can inspect `page_alto`, see that it depends on the `alto` service, and resolve the linked evidence to `tests/test_live.py::test_public_gallica_vertical_slice` and `tests/test_live.py::test_public_gallica_corpus_page_artifacts`.

Local handle constructors such as `Gallica.document()` do not require a public network test because they make no network request themselves.

## Authority

This evidence graph and its CI attestations describe what `gallica-sdk` has implemented and observed. BnF documentation and the public Gallica services remain authoritative. When documentation, implementation and live behavior disagree, the discrepancy should be recorded rather than hidden behind an abstraction.

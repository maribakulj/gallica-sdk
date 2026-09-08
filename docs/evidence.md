# Validation evidence and provenance

`gallica-sdk` distinguishes four things that are easy to conflate: implementation, evidence declaration, live observation and validation attestation.

A capability may exist in Python. The programmable reference links network-facing behavior to a stable live-test evidence ID. During a live run, the suite records what the public service actually did for every declared live-test evidence ID. Only after the complete suite passes can CI emit an attestation binding those observations to one exact commit and one exact GitHub Actions run.

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

Declarations are intentionally observation-free. They do not contain a CI timestamp, commit or run URL, because those facts belong to one execution rather than to the capability definition. The published schema still accepts the old optional observation fields so older schema-2.0 reference files remain readable, but the canonical reference no longer writes them.

## Live observations

When `GALLICA_LIVE_EVIDENCE_PATH` is set, the live suite writes one JSONL observation for every declared live-test evidence ID after the relevant assertions have succeeded. One pytest function may record more than one evidence ID when it validates independently classified services. The observation records:

- the stable evidence ID;
- the observation timestamp;
- `service_outcome` as either `operational` or `environment-limited`;
- an optional detail explaining the limitation.

This distinction matters for tests such as Categories and plain OCR. A test can pass because the SDK correctly rejects an HTML/403 or anti-bot response while the upstream service is still not reproducibly machine-accessible from that runner. A green test therefore does not automatically mean an operational service. Plain OCR has its own `live.text_access` evidence ID so an anti-bot response does not incorrectly downgrade ContentSearch or Issues validated by the same pytest function.

## CI attestations

After the complete live suite passes, CI runs:

```bash
python scripts/generate_evidence_attestation.py
```

The generator reads the JSONL observations and refuses to emit an attestation if any declared live-test evidence ID is missing, duplicated or unknown. The uploaded `evidence-attestation.json` uses schema 2.0 and contains:

- the exact commit SHA;
- the exact Actions run URL;
- generation timestamp;
- the observation timestamp for each live evidence ID;
- `test_outcome: passed` for the completed validation;
- the separately recorded `service_outcome`;
- the confidence label associated with the declaration;
- optional limitation detail.

CI uploads both the final attestation and the raw `live-evidence-results.jsonl` observations. No attestation is generated when the live-test step fails.

The normal CI live job emits the artifact for validated PR/push runs. A dedicated `Live evidence` workflow also runs every Sunday and can be started manually, so external service changes can be detected even when nobody commits code.

Schema-1.0 attestations remain loadable for compatibility. Because they only stored a generic `outcome`, their service outcome is normalized to `unknown` and they are not promoted to current operational evidence.

## Obtaining an attestation

**An attestation is a CI artifact, not a repository file.** `evidence-attestation.json`
is never committed: it is bound to one exact commit and one exact Actions run, so a
copy checked into the tree would immediately describe a different commit than the one
being read.

It is therefore not shipped in the wheel or the sdist, and a fresh clone contains no
attestation at all. To obtain one:

1. open the most recent successful `Live evidence` run (or the `live` job of a CI run)
   in GitHub Actions;
2. download the `gallica-evidence-attestation-<sha>` artifact;
3. pass the extracted `evidence-attestation.json` to `load_evidence_attestation()`.

Artifacts are retained for 30 days. Past that window the observations are gone and the
Sunday `Live evidence` run is what produces a current one.

The practical consequence is deliberate and worth stating directly: **for anyone who has
not downloaded an artifact, `evidence_freshness()` reports `unknown` for every live
evidence ID, and it is supposed to.** The freshness machinery is a tool for reasoning
about a validation run you hold, not a claim the package makes about itself. An SDK that
asserted "this service worked" from a value baked into its own source would be asserting
something it cannot know at import time.

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
    print(
        item["id"],
        item["state"],
        item["age_days"],
        item["service_outcome"],
    )
```

Possible freshness states remain `fresh`, `stale`, `failed`, `unknown` and `not-applicable`. `service_outcome` is reported separately, so a recent `environment-limited` observation is still a fresh observation without being mislabeled as operational. A successful current attestation becomes stale after the declaration's freshness window, currently 14 days for the live tests. That window is project policy, not a BnF guarantee.

Operational contracts accept the same attestation:

```python
from gallica import operational_contract

contract = operational_contract("page_alto", attestation=attestation)
```

Without it, the contract still knows its services and evidence targets, but reports live freshness as `unknown`.

## Capability links

Every public capability has exactly one `capability_evidence` record. It identifies the Gallica service IDs involved, the evidence IDs that validate the behavior, and an optional minimal example.

For example, an agent can inspect `page_alto`, see that it depends on the `alto` service, and resolve the linked evidence to `tests/test_live.py::test_public_gallica_vertical_slice` and `tests/test_live.py::test_public_gallica_corpus_page_artifacts`.

Local handle constructors such as `Gallica.document()` do not require a public network test because they make no network request themselves.

## Authority

This evidence graph and its CI attestations describe what `gallica-sdk` has implemented and observed. BnF documentation and the public Gallica services remain authoritative. When documentation, implementation and live behavior disagree, the discrepancy should be recorded rather than hidden behind an abstraction.

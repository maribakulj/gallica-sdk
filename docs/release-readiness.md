# First release readiness

`gallica-sdk` has not published a stable GitHub or PyPI release yet. The current package version is a development version.

## Already in place

- [x] typed public Python API;
- [x] unit and simulated integration tests;
- [x] deterministic non-live branch coverage gate with an 85% floor;
- [x] live smoke tests against public Gallica services;
- [x] weekly live-evidence revalidation workflow;
- [x] CI-generated evidence attestations tied to exact commits and Actions runs;
- [x] Python 3.11, 3.12, 3.13 and 3.14 CI on Linux;
- [x] Windows and macOS corpus/CLI smoke tests on Python 3.14;
- [x] GitHub Actions upgraded to current maintained majors and pinned to exact commit SHAs;
- [x] Ruff and mypy strict;
- [x] wheel and sdist build validation;
- [x] `twine check` metadata validation;
- [x] isolated wheel installation and `pip check`;
- [x] isolated sdist installation and `pip check`;
- [x] resumable corpus workflow with request fingerprints, checksums and failure provenance;
- [x] machine-readable capability contracts;
- [x] resolved operational contracts for agents;
- [x] programmable reference and executable JSON Schema validation;
- [x] validation evidence graph with historical provenance plus current CI attestations;
- [x] minimal JSON-first CLI tested from wheel and sdist;
- [x] project changelog;
- [x] package metadata URLs and classifiers;
- [x] user-facing guides for search, documents, periodicals, corpus, quotas, errors and CLI;
- [x] executable reference notebooks validated in CI;
- [x] release metadata/tag validator;
- [x] non-publishing release-candidate workflow retaining validated artifacts;
- [x] desired `main` repository ruleset versioned and tested in `repository-policy/main-ruleset.json`.

## Blocking the first public release

- [ ] apply the desired repository ruleset or equivalent branch protection to `main` and verify that GitHub enforces it;
- [ ] choose and add an explicit open-source license;
- [ ] choose the first public version/tag policy and remove the `.dev0` suffix for the release commit;
- [ ] configure protected PyPI credentials or Trusted Publishing and add the final publish boundary;
- [ ] validate the final release artifact through TestPyPI or an equivalent isolated publication path.

The checked-in governance manifest is not itself protection. GitHub must report an active rule on `main`; otherwise a direct push can still bypass the CI gates. See [`repository-governance.md`](repository-governance.md) and issue #25.

## Important non-blockers

The following features are intentionally not required for the first release:

- PDF support;
- MCP;
- async API;
- Parquet/DataFrame integration;
- implicit all-page corpus downloads;
- generalized concurrency.

A missing feature is not a release blocker when the project documents it accurately and does not expose an unsupported public contract.

## Release principle

The first release should be small enough that every network-facing capability remains tied to a maintained live test. Publishing more endpoints simply to increase feature count would weaken the main property of the project: a capability is advertised only when its operational behavior has been observed and validated.

The coverage floor is a regression guard, not a target to game. New tests should continue to prove behavior and failure modes; adding trivial lines merely to inflate the percentage would defeat the point with impressive bureaucratic efficiency.

Detailed procedure: [`releasing.md`](releasing.md).

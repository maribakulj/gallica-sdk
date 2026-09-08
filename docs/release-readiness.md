# First release readiness

`gallica-sdk` is now at `0.2.0rc1`, the first public release candidate. No stable GitHub or PyPI release has been published yet.

## Already in place

- [x] typed public Python API;
- [x] audited 0.2 public API boundary with root exports, facade signatures and public model fields locked by deterministic tests;
- [x] Apache License 2.0 declared in the repository and package metadata;
- [x] wheel and sdist license-file / `License-Expression` validation in CI;
- [x] first release-candidate version selected and `.dev0` removed;
- [x] guarded TestPyPI Trusted Publishing job implemented separately from build machinery;
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
- [x] validation evidence graph with current CI attestations;
- [x] JSON-first CLI tested from wheel and sdist;
- [x] project changelog;
- [x] package metadata URLs and classifiers;
- [x] user-facing guides for search, documents, periodicals, corpus, quotas, errors and CLI;
- [x] executable reference notebooks validated in CI;
- [x] release metadata/tag validator;
- [x] release-candidate workflow retaining the exact validated wheel/sdist artifacts;
- [x] desired `main` repository ruleset versioned and tested in `repository-policy/main-ruleset.json`.

## Blocking the first stable public release

- [ ] apply the desired repository ruleset or equivalent branch protection to `main` and verify that GitHub enforces it;
- [ ] configure the `testpypi` GitHub environment and matching TestPyPI Trusted Publisher for `.github/workflows/release-candidate.yml`;
- [ ] set the repository variable `TESTPYPI_PUBLISH_ENABLED=true` only after that Trusted Publisher is configured;
- [ ] run the release-candidate workflow from `main` with `publish_testpypi=true` and verify installation of `gallica-sdk==0.2.0rc1` from TestPyPI;
- [ ] promote the validated candidate to final version `0.2.0` and create the matching `v0.2.0` tag;
- [ ] configure the protected production PyPI Trusted Publisher and final publish boundary.

The checked-in governance manifest is not itself protection. GitHub currently reports `main` as unprotected and reports no active repository ruleset. See [`repository-governance.md`](repository-governance.md) and issue #25.

The audited Python boundary is documented in [`public-api.md`](public-api.md). The locking tests are intentional release guards: changing a public export, facade signature or public result-model field after 0.2.0 should require an explicit compatibility decision rather than occurring as a refactor side effect.

The project license is Apache-2.0. `scripts/validate_release.py` checks source metadata and `scripts/validate_distributions.py` checks that both built distribution formats carry the SPDX license expression and the `LICENSE` file.

## TestPyPI publication boundary

The release-candidate workflow builds and validates distributions in a job with read-only repository permissions. A separate `publish-testpypi` job may receive `id-token: write`, but only when all of the following are true:

- the workflow was started manually;
- `publish_testpypi=true` was explicitly selected;
- the workflow runs from `main`;
- the repository variable `TESTPYPI_PUBLISH_ENABLED` is exactly `true`;
- the `testpypi` environment and matching TestPyPI Trusted Publisher have been configured externally.

The publishing job does not check out the repository or run build scripts. It downloads the exact `gallica-sdk-dist` artifact produced by the validated build job and publishes those bytes to TestPyPI.

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

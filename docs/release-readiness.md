# First release readiness

`gallica-sdk` has not published a stable GitHub or PyPI release yet. The current package version is a development version.

## Already in place

- [x] typed public Python API;
- [x] unit and simulated integration tests;
- [x] live smoke tests against public Gallica services;
- [x] Python 3.11 and 3.12 CI;
- [x] Ruff and mypy strict;
- [x] wheel and sdist build validation;
- [x] wheel reinstall smoke check;
- [x] resumable corpus workflow;
- [x] machine-readable capability contracts;
- [x] programmable reference and JSON Schema;
- [x] validation evidence graph with dated CI provenance;
- [x] project changelog;
- [x] package metadata URLs and classifiers.

## Blocking the first public release

- [ ] choose and add an explicit open-source license;
- [ ] choose the first public version/tag policy and remove the `.dev0` suffix for the release commit;
- [ ] create a release workflow with protected publishing credentials or trusted publishing;
- [ ] validate the final artifact on TestPyPI or an equivalent isolated installation path;
- [ ] finish the user-facing documentation/notebook pass planned after Phase 10.

## Important non-blockers

The following features are intentionally not required for the first release:

- PDF support;
- CLI;
- MCP;
- async API;
- Parquet/DataFrame integration;
- implicit all-page corpus downloads;
- generalized concurrency.

A missing feature is not a release blocker when the project documents it accurately and does not expose an unsupported public contract.

## Release principle

The first release should be small enough that every network-facing capability remains tied to a maintained live test. Publishing more endpoints simply to increase feature count would weaken the main property of the project: a capability is advertised only when its operational behavior has been observed and validated.

# Releasing gallica-sdk

The repository separates release validation from publication. Building a valid artifact must not require PyPI credentials, and publication must never happen as an accidental side effect of ordinary CI.

The project is distributed under the Apache License 2.0. Source metadata and built distribution artifacts must agree on that license before any candidate can be treated as releasable.

## Current candidate

The current package version is `0.2.0rc1`. This is the first release candidate for the intended `0.2.0` stable release.

Normal CI validates the candidate with:

```bash
python scripts/validate_release.py
python -m build
twine check dist/*
python scripts/validate_distributions.py dist/*
```

`validate_release.py` checks the repository-level SPDX declaration and `LICENSE` file. `validate_distributions.py` then inspects the built wheel and sdist, requiring `License-Expression: Apache-2.0`, `License-File: LICENSE`, and the Apache-2.0 license text inside both archive formats.

CI installs both the wheel and the source distribution into separate virtual environments and runs `pip check` plus import/version smoke checks.

## Release candidate workflow

`.github/workflows/release-candidate.yml` builds and validates non-development versions. A manual run now executes `validate_release.py --require-release`; a Git tag additionally requires the tag and project version to match exactly.

Examples:

```text
project.version = 0.2.0rc1
manual candidate run  -> accepted
v0.2.0rc1             -> accepted
v0.2.0                -> rejected while project.version is 0.2.0rc1
0.2.0.dev0            -> rejected by --require-release
```

The build job retains the wheel and sdist as the `gallica-sdk-dist` Actions artifact. Publication jobs must consume that artifact rather than rebuild different bytes.

## TestPyPI Trusted Publishing

The workflow contains an optional `publish-testpypi` job. It is intentionally separated from the build job and receives `id-token: write` only in that publishing job.

Before enabling it, configure all of the following outside the repository source tree:

1. create a GitHub environment named `testpypi`;
2. configure a TestPyPI Trusted Publisher for repository `maribakulj/gallica-sdk`;
3. set its workflow filename to `release-candidate.yml` and environment to `testpypi`;
4. set repository variable `TESTPYPI_PUBLISH_ENABLED=true` only after the publisher is configured.

Then run **Release candidate** manually from `main` with `publish_testpypi=true`.

The publish job has four code-level gates in addition to the external Trusted Publisher configuration: it must be a manual workflow run, `publish_testpypi` must be true, the ref must be `main`, and `TESTPYPI_PUBLISH_ENABLED` must equal `true`.

The publishing job performs no checkout and no build. It downloads `gallica-sdk-dist` from the preceding job and sends those exact artifacts to TestPyPI using the PyPA publish action pinned to a full commit SHA.

After a successful upload, validate from a clean environment against TestPyPI. Because runtime dependency `httpx` is not expected to be mirrored there, allow dependencies to come from normal PyPI while selecting the candidate from TestPyPI, for example:

```bash
python -m venv /tmp/gallica-testpypi
/tmp/gallica-testpypi/bin/python -m pip install \
  --index-url https://pypi.org/simple \
  --extra-index-url https://test.pypi.org/simple \
  'gallica-sdk==0.2.0rc1'
/tmp/gallica-testpypi/bin/gallica capabilities
```

The candidate must report `0.2.0rc1`, expose the expected CLI and import cleanly before promotion to the stable version.

## Before the first stable public release

The final release commit must satisfy all of the following:

1. Apache-2.0 repository and package metadata agree and both distribution formats contain the license;
2. `main` is protected by an enforced repository ruleset or equivalent branch protection;
3. `0.2.0rc1` has been published and installed successfully through TestPyPI;
4. candidate feedback requires no incompatible public API change, or any such change is reflected in a new candidate;
5. `project.version` is promoted to `0.2.0`;
6. the intended tag is exactly `v0.2.0`;
7. normal CI is green, including live Gallica tests and executable notebooks;
8. the release workflow validates wheel and sdist;
9. production PyPI publication uses a protected Trusted Publisher and consumes validated artifacts rather than rebuilding them.

## Production publication boundary

Production PyPI publishing remains intentionally absent. Preparing TestPyPI does not silently enable production publishing, because conflating the rehearsal stage and the irreversible public release would be a particularly efficient way to make packaging exciting for all the wrong reasons.

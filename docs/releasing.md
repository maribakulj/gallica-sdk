# Releasing gallica-sdk

The repository separates release validation from publication. Building a valid artifact must not require PyPI credentials, and publication must never happen as an accidental side effect of ordinary CI.

The project is distributed under the Apache License 2.0. Source metadata and built distribution artifacts must agree on that license before any candidate can be treated as releasable.

## Development validation

Normal CI validates the current development version with:

```bash
python scripts/validate_release.py
python -m build
twine check dist/*
python scripts/validate_distributions.py dist/*
```

`validate_release.py` checks the repository-level SPDX declaration and `LICENSE` file. `validate_distributions.py` then inspects the built wheel and sdist, requiring `License-Expression: Apache-2.0`, `License-File: LICENSE`, and the Apache-2.0 license text inside both archive formats.

CI then installs both the wheel and the source distribution into separate virtual environments and runs `pip check` plus import/version smoke checks.

## Release candidate workflow

`.github/workflows/release-candidate.yml` is intentionally non-publishing. It can be run manually while the project still carries a development version. On a Git tag it additionally requires the tag and project version to match exactly.

Examples:

```text
project.version = 0.2.0
v0.2.0              -> accepted
0.2.0               -> accepted by the validator when supplied explicitly
v0.2.1              -> rejected
0.2.0.dev0 + v0.2.0 -> rejected
```

Successful runs retain the wheel and sdist as a GitHub Actions artifact. The same artifact bytes should be the ones later exercised through TestPyPI and ultimately published; rebuilding after validation would defeat the point of validating a candidate.

## Before the first public release

The release commit must satisfy all of the following:

1. Apache-2.0 repository and package metadata agree and both distribution formats contain the license;
2. `project.version` is a non-development version;
3. the intended tag matches that version;
4. normal CI is green, including live Gallica tests and executable notebooks;
5. the release-candidate workflow validates wheel and sdist;
6. the final artifact is tested through TestPyPI or another isolated publication path;
7. PyPI publication uses protected credentials or Trusted Publishing;
8. `main` is protected by an enforced repository ruleset or equivalent branch protection.

## Publication boundary

This repository currently contains no automatic PyPI upload step. That omission is deliberate until the first public version, TestPyPI validation and publishing trust configuration have been completed.

When publication is added, the publish job should consume artifacts produced by a preceding validation job rather than rebuilding different bytes after validation.

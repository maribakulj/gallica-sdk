# Releasing gallica-sdk

The repository separates release validation from publication. Building a valid artifact must not require PyPI credentials, and publication must never happen as an accidental side effect of ordinary CI.

## Development validation

Normal CI validates the current development version with:

```bash
python scripts/validate_release.py
python -m build
twine check dist/*
```

It then installs both the wheel and the source distribution into separate virtual environments and runs `pip check` plus import/version smoke checks.

## Release candidate workflow

`.github/workflows/release-candidate.yml` is intentionally non-publishing. It can be run manually while the project still carries a development version. On a Git tag it additionally requires the tag and project version to match exactly.

Examples:

```text
project.version = 0.1.0
v0.1.0              -> accepted
0.1.0               -> accepted by the validator when supplied explicitly
v0.1.1              -> rejected
0.1.0.dev0 + v0.1.0 -> rejected
```

Successful runs retain the wheel and sdist as a GitHub Actions artifact.

## Before the first public release

The release commit must satisfy all of the following:

1. an explicit project license has been chosen and added;
2. `project.version` is a non-development version;
3. the intended tag matches that version;
4. normal CI is green, including live Gallica tests and executable notebooks;
5. the release-candidate workflow validates wheel and sdist;
6. the final artifact is tested through TestPyPI or another isolated publication path;
7. PyPI publication uses protected credentials or Trusted Publishing.

## Publication boundary

This repository currently contains no automatic PyPI upload step. That omission is deliberate until the license, first public version, and publishing trust configuration have been decided.

When publication is added, the publish job should consume artifacts produced by a preceding validation job rather than rebuilding different bytes after validation.

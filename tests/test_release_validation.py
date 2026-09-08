from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path("scripts/validate_release.py")
spec = importlib.util.spec_from_file_location("validate_release", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_release_candidate_metadata_is_valid() -> None:
    assert module.validate() == "0.2.0rc1"
    assert module.validate(require_release=True) == "0.2.0rc1"
    assert module.validate(tag="v0.2.0rc1") == "0.2.0rc1"


def test_development_version_is_rejected_for_release(monkeypatch: pytest.MonkeyPatch) -> None:
    project = dict(module.project_metadata())
    project["version"] = "0.2.0.dev0"
    monkeypatch.setattr(module, "project_metadata", lambda: project)

    assert module.validate() == "0.2.0.dev0"
    with pytest.raises(ValueError, match="development version"):
        module.validate(require_release=True)


def test_tag_must_match_project_version() -> None:
    with pytest.raises(ValueError, match="does not match"):
        module.validate(tag="v9.9.9")

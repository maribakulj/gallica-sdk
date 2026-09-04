from __future__ import annotations

import tomllib
from importlib.metadata import version
from pathlib import Path

from gallica import __version__, programmable_reference

ROOT = Path(__file__).resolve().parents[1]


def _project_metadata() -> dict[str, object]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    assert isinstance(project, dict)
    return project


def test_distribution_version_is_single_installed_truth() -> None:
    project = _project_metadata()
    assert __version__ == version("gallica-sdk")
    assert __version__ == project["version"]


def test_readme_tracks_project_and_reference_versions() -> None:
    project = _project_metadata()
    reference = programmable_reference()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert f"**{project['version']} " in readme
    assert f"`schema_version: {reference['schema_version']}`" in readme
    assert "schema_version: 1.0" not in readme


def test_package_metadata_matches_current_positioning() -> None:
    project = _project_metadata()
    description = project["description"]
    urls = project["urls"]

    assert isinstance(description, str)
    assert "programmable reference" in description.lower()
    assert isinstance(urls, dict)
    assert urls["Source"] == "https://github.com/maribakulj/gallica-sdk"
    assert urls["Issues"] == "https://github.com/maribakulj/gallica-sdk/issues"


def test_release_blockers_are_explicit_not_implicit() -> None:
    checklist = (ROOT / "docs/release-readiness.md").read_text(encoding="utf-8")
    assert "choose and add an explicit open-source license" in checklist
    assert "remove the `.dev0` suffix" in checklist
    assert "TestPyPI" in checklist

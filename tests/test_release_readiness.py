from __future__ import annotations

import re
import tomllib
from importlib.metadata import version
from pathlib import Path

from gallica import __version__, programmable_reference

ROOT = Path(__file__).resolve().parents[1]
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def _project_metadata() -> dict[str, object]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    assert isinstance(project, dict)
    return project


def _project_config() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


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


def test_python_classifiers_cover_tested_versions() -> None:
    project = _project_metadata()
    classifiers = project["classifiers"]
    assert isinstance(classifiers, list)
    for python_version in ("3.11", "3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {python_version}" in classifiers


def test_all_external_workflow_actions_are_pinned_to_full_sha() -> None:
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows
    for workflow in workflows:
        for raw_line in workflow.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped.startswith("- uses:") and not stripped.startswith("uses:"):
                continue
            action = stripped.split("uses:", 1)[1].strip().split()[0]
            if action.startswith("./"):
                continue
            _owner_action, separator, ref = action.rpartition("@")
            assert separator, f"missing action ref in {workflow}: {action}"
            assert FULL_SHA.fullmatch(ref), f"unpinned action in {workflow}: {action}"


def test_non_live_coverage_floor_is_enforced_in_ci() -> None:
    config = _project_config()
    tool = config["tool"]
    assert isinstance(tool, dict)
    coverage = tool["coverage"]
    assert isinstance(coverage, dict)
    report = coverage["report"]
    run = coverage["run"]
    assert isinstance(report, dict)
    assert isinstance(run, dict)
    assert report["fail_under"] >= 85
    assert run["branch"] is True

    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "  coverage:\n" in ci
    assert "pytest -m 'not live' --cov=gallica --cov-report=term-missing" in ci


def test_release_blockers_are_explicit_not_implicit() -> None:
    checklist = (ROOT / "docs/release-readiness.md").read_text(encoding="utf-8")
    assert "choose and add an explicit open-source license" in checklist
    assert "remove the `.dev0` suffix" in checklist
    assert "TestPyPI" in checklist

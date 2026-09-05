from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?$")


def project_metadata() -> dict[str, object]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml has no [project] table")
    return project


def validate(*, tag: str | None = None, require_release: bool = False) -> str:
    project = project_metadata()
    version = project.get("version")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise ValueError("project.version must be an explicit PEP 440-style version string")

    required_text = ("name", "description", "readme", "requires-python")
    for key in required_text:
        value = project.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"project.{key} must be a non-empty string")

    urls = project.get("urls")
    if not isinstance(urls, dict) or not {"Homepage", "Source", "Issues"} <= set(urls):
        raise ValueError("project.urls must define Homepage, Source and Issues")

    if tag is not None:
        normalized_tag = tag[1:] if tag.startswith("v") else tag
        if normalized_tag != version:
            raise ValueError(f"tag {tag!r} does not match project version {version!r}")
        require_release = True

    if require_release and ".dev" in version:
        raise ValueError("release artifacts cannot use a development version")

    return version


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate gallica-sdk release metadata.")
    parser.add_argument("--tag", help="Git tag to compare with project.version, e.g. v0.1.0")
    parser.add_argument(
        "--require-release",
        action="store_true",
        help="Reject development versions even when no tag is supplied.",
    )
    args = parser.parse_args()
    version = validate(tag=args.tag, require_release=args.require_release)
    print(version)


if __name__ == "__main__":
    main()

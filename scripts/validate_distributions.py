from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

EXPECTED_LICENSE = "Apache-2.0"
LICENSE_MARKERS = ("Apache License", "Version 2.0, January 2004")


def _validate_metadata(text: str, *, artifact: Path) -> None:
    if f"License-Expression: {EXPECTED_LICENSE}" not in text:
        raise ValueError(f"{artifact.name} metadata lacks License-Expression: {EXPECTED_LICENSE}")
    if "License-File: LICENSE" not in text:
        raise ValueError(f"{artifact.name} metadata does not declare LICENSE as a license file")


def _validate_license_text(text: str, *, artifact: Path) -> None:
    if not all(marker in text for marker in LICENSE_MARKERS):
        raise ValueError(f"{artifact.name} does not contain the expected Apache-2.0 license text")


def validate_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise ValueError(f"{path.name} must contain exactly one dist-info/METADATA")
        _validate_metadata(
            archive.read(metadata_names[0]).decode("utf-8"),
            artifact=path,
        )

        license_names = [
            name
            for name in names
            if name.endswith(".dist-info/licenses/LICENSE") or name == "LICENSE"
        ]
        if not license_names:
            raise ValueError(f"{path.name} does not contain LICENSE")
        _validate_license_text(
            archive.read(license_names[0]).decode("utf-8"),
            artifact=path,
        )


def validate_sdist(path: Path) -> None:
    with tarfile.open(path, mode="r:gz") as archive:
        names = archive.getnames()
        metadata_names = [name for name in names if name.endswith("/PKG-INFO")]
        if len(metadata_names) != 1:
            raise ValueError(f"{path.name} must contain exactly one PKG-INFO")
        metadata_file = archive.extractfile(metadata_names[0])
        if metadata_file is None:
            raise ValueError(f"{path.name} PKG-INFO could not be read")
        _validate_metadata(metadata_file.read().decode("utf-8"), artifact=path)

        license_names = [name for name in names if name.endswith("/LICENSE")]
        if not license_names:
            raise ValueError(f"{path.name} does not contain LICENSE")
        license_file = archive.extractfile(license_names[0])
        if license_file is None:
            raise ValueError(f"{path.name} LICENSE could not be read")
        _validate_license_text(license_file.read().decode("utf-8"), artifact=path)


def validate_distributions(paths: list[Path]) -> None:
    wheels = [path for path in paths if path.suffix == ".whl"]
    sdists = [path for path in paths if path.name.endswith(".tar.gz")]
    if not wheels or not sdists:
        raise ValueError("expected at least one wheel and one .tar.gz sdist")

    for path in wheels:
        validate_wheel(path)
    for path in sdists:
        validate_sdist(path)


def main() -> None:
    paths = [Path(value) for value in sys.argv[1:]]
    if not paths:
        raise SystemExit("usage: validate_distributions.py DIST [DIST ...]")
    validate_distributions(paths)
    print(f"validated {len(paths)} distribution artifact(s) with {EXPECTED_LICENSE}")


if __name__ == "__main__":
    main()

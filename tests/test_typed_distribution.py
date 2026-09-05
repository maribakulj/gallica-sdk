from __future__ import annotations

from pathlib import Path


def test_pep561_marker_is_checked_in() -> None:
    marker = Path("src/gallica/py.typed")
    assert marker.is_file()

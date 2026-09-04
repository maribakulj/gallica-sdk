from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def execute_notebook(path: Path) -> None:
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=180,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    )
    client.execute()


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        paths = sorted(Path("notebooks").glob("*.ipynb"))
    if not paths:
        raise SystemExit("No notebooks found")

    for path in paths:
        print(f"Executing {path}")
        execute_notebook(path)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DOCS = (
    "docs/getting-started.md",
    "docs/search.md",
    "docs/documents.md",
    "docs/periodicals.md",
    "docs/corpus.md",
    "docs/quotas.md",
    "docs/errors.md",
    "docs/cli.md",
    "docs/architecture.md",
    "docs/capabilities.md",
    "docs/agents.md",
    "docs/evidence.md",
    "docs/release-readiness.md",
    "docs/releasing.md",
)

EXPECTED_NOTEBOOKS = (
    "notebooks/01_search_and_metadata.ipynb",
    "notebooks/02_resumable_corpus.ipynb",
)


def test_user_documentation_is_linked_from_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for relative_path in EXPECTED_DOCS:
        assert (ROOT / relative_path).exists(), relative_path
        assert relative_path in readme, relative_path


def test_readme_does_not_claim_existing_cli_is_missing() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/cli.md" in readme
    missing_section = readme.partition("## Pas encore dans la 0.2")[2]
    assert "- CLI" not in missing_section


def test_reference_notebooks_are_valid_json_with_compilable_code() -> None:
    for relative_path in EXPECTED_NOTEBOOKS:
        path = ROOT / relative_path
        notebook = json.loads(path.read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        assert notebook["cells"], relative_path

        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        assert code_cells, relative_path
        for cell in code_cells:
            source = "".join(cell["source"])
            compile(source, f"{relative_path}:cell", "exec")


def test_notebooks_are_linked_from_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for relative_path in EXPECTED_NOTEBOOKS:
        assert relative_path in readme, relative_path

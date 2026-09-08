from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gallica import capabilities, programmable_reference

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


def test_generated_capability_documentation_is_current() -> None:
    subprocess.run(
        [sys.executable, "scripts/generate_docs.py", "--check"],
        cwd=ROOT,
        check=True,
    )


def test_every_canonical_capability_is_visible_in_human_docs() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/capabilities.md").read_text(encoding="utf-8")
    for spec in capabilities():
        assert spec["call"] in readme, spec["id"]
        assert spec["call"] in matrix, spec["id"]


def test_human_docs_do_not_claim_the_existing_cli_is_missing() -> None:
    """The CLI ships; no human doc may still describe it as absent or conditional.

    The generated capability blocks cannot catch this: prose about what the
    project deliberately does *not* do is hand-written everywhere.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/cli.md" in readme
    assert "- CLI" not in readme.partition("## Non-objectifs actuels")[2]

    architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
    assert "cli.md" in architecture
    non_goals = architecture.partition("## Non-objectifs actuels")[2]
    assert "- CLI" not in non_goals
    assert "Une CLI, une API async" not in architecture


def test_architecture_functional_surface_lists_every_network_service() -> None:
    """docs/architecture.md prose must not lag behind the canonical service catalog."""
    architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
    surface = architecture.partition("## Surface fonctionnelle actuelle")[2]
    surface = surface.partition("## ")[0]
    expected_markers = {
        "sru": "SRU",
        "categories": "Categories",
        "oai-record": "OAIRecord",
        "pagination": "Pagination",
        "toc": "Toc",
        "issues": "Issues",
        "content-search": "ContentSearch",
        "text": "OCR",
        "alto": "ALTO",
        "iiif-image": "IIIF Image",
        "iiif-presentation": "IIIF Presentation",
    }
    supported = {
        service["id"]
        for service in programmable_reference()["services"]
        if service["status"] != "not-supported"
    }
    assert supported == set(expected_markers), supported.symmetric_difference(expected_markers)
    for service_id, marker in expected_markers.items():
        assert marker in surface, service_id


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

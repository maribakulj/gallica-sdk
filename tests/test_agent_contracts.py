from __future__ import annotations

import inspect
import json
from pathlib import Path

from gallica import Corpus, Document, Gallica, Page, Periodical
from gallica.agent import capabilities

PUBLIC_CLASSES = {
    "Gallica": Gallica,
    "Document": Document,
    "Page": Page,
    "Periodical": Periodical,
    "Corpus": Corpus,
}


def test_capabilities_are_unique_json_serializable_and_exposed() -> None:
    specs = capabilities()
    ids = [spec["id"] for spec in specs]
    assert len(ids) == len(set(ids))
    assert Gallica.capabilities() == specs
    payload = json.loads(json.dumps(specs))
    assert len(payload) == len(specs)


def test_declared_calls_exist_on_public_classes() -> None:
    for spec in capabilities():
        class_name, method_name = spec["call"].split(".", 1)
        assert class_name in PUBLIC_CLASSES
        assert hasattr(PUBLIC_CLASSES[class_name], method_name), spec["call"]


def test_declared_parameters_match_public_signatures() -> None:
    for spec in capabilities():
        class_name, method_name = spec["call"].split(".", 1)
        method = getattr(PUBLIC_CLASSES[class_name], method_name)
        signature = inspect.signature(method)
        actual_names = {
            name
            for name in signature.parameters
            if name not in {"self", "cls"}
        }
        declared_names = {parameter["name"] for parameter in spec["parameters"]}
        assert declared_names == actual_names, spec["call"]


def test_object_construction_is_part_of_the_contract() -> None:
    by_id = {spec["id"]: spec for spec in capabilities()}
    assert by_id["document"]["call"] == "Gallica.document"
    assert by_id["periodical"]["call"] == "Gallica.periodical"
    assert by_id["corpus"]["call"] == "Gallica.corpus"


def test_required_agent_safeguards_are_machine_readable() -> None:
    by_id = {spec["id"]: spec for spec in capabilities()}
    assert "maximum_records must be between 1 and 50" in by_id["search"]["constraints"]
    assert "width > 1000 uses the HD rate bucket" in by_id["page_image"]["constraints"]
    assert "there is no implicit all-pages mode" in by_id["corpus_fetch"]["constraints"]


def test_recipes_only_reference_known_capabilities() -> None:
    recipes_path = Path("agent/recipes.json")
    payload = json.loads(recipes_path.read_text(encoding="utf-8"))
    known = {spec["id"] for spec in capabilities()}
    assert payload["recipes"]
    for recipe in payload["recipes"]:
        assert recipe["capabilities"]
        assert set(recipe["capabilities"]) <= known

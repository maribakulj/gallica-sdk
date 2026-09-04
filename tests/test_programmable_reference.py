from __future__ import annotations

import json
from pathlib import Path

from gallica.agent import capabilities
from gallica.reference import REFERENCE_SCHEMA_VERSION, programmable_reference


def test_checked_in_reference_matches_canonical_python() -> None:
    checked_in = json.loads(Path("reference/gallica-reference.json").read_text(encoding="utf-8"))
    canonical = json.loads(json.dumps(programmable_reference()))
    assert checked_in == canonical


def test_reference_indexes_every_capability_exactly_once() -> None:
    reference = programmable_reference()
    expected = [(spec["id"], spec["call"]) for spec in capabilities()]
    actual = [(item["id"], item["call"]) for item in reference["capability_index"]]
    assert actual == expected
    assert len(actual) == len(set(actual))


def test_service_ids_are_unique_and_statuses_explicit() -> None:
    services = programmable_reference()["services"]
    ids = [service["id"] for service in services]
    assert len(ids) == len(set(ids))
    assert {service["status"] for service in services} <= {"live-validated", "not-supported"}
    assert any(service["id"] == "pdf" and service["status"] == "not-supported" for service in services)


def test_evidence_graph_resolves_all_references() -> None:
    reference = programmable_reference()
    capability_ids = {item["id"] for item in reference["capability_index"]}
    service_ids = {item["id"] for item in reference["services"]}
    evidence_ids = {item["id"] for item in reference["evidence"]}

    mappings = reference["capability_evidence"]
    assert {item["capability"] for item in mappings} == capability_ids
    assert len(mappings) == len(capability_ids)

    for item in mappings:
        assert set(item["services"]) <= service_ids
        assert set(item["evidence"]) <= evidence_ids
        if item["example"] is not None:
            assert item["example"] in evidence_ids


def test_live_validated_network_capabilities_have_live_evidence() -> None:
    reference = programmable_reference()
    live_ids = {
        item["id"]
        for item in reference["evidence"]
        if item["kind"] == "live-test" and item["status"] == "passing-in-ci"
    }
    network_service_ids = {
        item["id"] for item in reference["services"] if item["status"] == "live-validated"
    }

    for item in reference["capability_evidence"]:
        if set(item["services"]) & network_service_ids:
            assert set(item["evidence"]) & live_ids, item["capability"]


def test_evidence_targets_exist_in_repository() -> None:
    for item in programmable_reference()["evidence"]:
        path = item["target"].split("::", 1)[0]
        assert Path(path).exists(), item["target"]


def test_reference_schema_version_is_v1_1() -> None:
    assert REFERENCE_SCHEMA_VERSION == "1.1"
    schema = json.loads(Path("reference/schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["id"]["const"] == "gallica-sdk-reference"
    assert "evidence" in schema["required"]
    assert "capability_evidence" in schema["required"]

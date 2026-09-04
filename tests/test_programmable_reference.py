from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from gallica.agent import capabilities
from gallica.evidence import evidence_freshness
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
    live_ids = {item["id"] for item in reference["evidence"] if item["kind"] == "live-test" and item["status"] == "passing-in-ci"}
    network_service_ids = {item["id"] for item in reference["services"] if item["status"] == "live-validated"}
    for item in reference["capability_evidence"]:
        if set(item["services"]) & network_service_ids:
            assert set(item["evidence"]) & live_ids, item["capability"]


def test_live_evidence_has_observation_provenance() -> None:
    for item in programmable_reference()["evidence"]:
        if item["kind"] != "live-test":
            continue
        assert item["observed_at"].endswith("Z")
        assert len(item["observed_commit"]) == 40
        assert item["observed_run"].startswith("https://github.com/")
        assert item["freshness_days"] >= 1
        assert item["confidence"] in {"high", "medium", "low"}


def test_evidence_freshness_changes_without_rewriting_history() -> None:
    fresh = {item["id"]: item for item in evidence_freshness(as_of=date(2026, 9, 4))}
    stale = {item["id"]: item for item in evidence_freshness(as_of=date(2026, 10, 1))}
    assert fresh["live.vertical_slice"]["state"] == "fresh"
    assert fresh["live.vertical_slice"]["age_days"] == 0
    assert stale["live.vertical_slice"]["state"] == "stale"
    assert stale["live.vertical_slice"]["age_days"] == 27
    assert fresh["example.search_to_corpus"]["state"] == "not-applicable"


def test_evidence_targets_exist_in_repository() -> None:
    for item in programmable_reference()["evidence"]:
        path_text, separator, node = item["target"].partition("::")
        path = Path(path_text)
        assert path.exists(), item["target"]
        if separator:
            source = path.read_text(encoding="utf-8")
            assert f"def {node}(" in source, item["target"]


def test_reference_schema_version_is_v2_0() -> None:
    assert REFERENCE_SCHEMA_VERSION == "2.0"
    reference = programmable_reference()
    assert reference["operational_contracts_export"] == "python scripts/export_operational_contracts.py"

    schema = json.loads(Path("reference/schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["id"]["const"] == "gallica-sdk-reference"
    assert "operational_contracts_export" in schema["required"]
    assert "observed_at" in schema["properties"]["evidence"]["items"]["properties"]
    assert "freshness_days" in schema["properties"]["evidence"]["items"]["properties"]

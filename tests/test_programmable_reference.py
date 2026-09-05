from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from gallica.agent import capabilities
from gallica.evidence import build_evidence_attestation, evidence_freshness
from gallica.reference import REFERENCE_SCHEMA_VERSION, programmable_reference


def _checked_in_reference() -> dict[str, object]:
    payload = json.loads(Path("reference/gallica-reference.json").read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _reference_schema() -> dict[str, object]:
    payload = json.loads(Path("reference/schema.json").read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_checked_in_reference_matches_canonical_python() -> None:
    checked_in = _checked_in_reference()
    canonical = json.loads(json.dumps(programmable_reference()))
    assert checked_in == canonical


def test_checked_in_reference_validates_against_published_schema() -> None:
    schema = _reference_schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(_checked_in_reference()), key=lambda item: list(item.path))
    assert errors == []


def test_schema_rejects_an_invalid_service_status() -> None:
    payload = _checked_in_reference()
    services = payload["services"]
    assert isinstance(services, list)
    first = services[0]
    assert isinstance(first, dict)
    first["status"] = "looks-fine-to-me"
    validator = Draft202012Validator(_reference_schema())
    errors = list(validator.iter_errors(payload))
    assert any(isinstance(error, ValidationError) for error in errors)


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
    assert {service["status"] for service in services} <= {
        "live-validated",
        "environment-limited",
        "not-supported",
    }
    assert any(service["id"] == "pdf" and service["status"] == "not-supported" for service in services)
    assert any(
        service["id"] == "text" and service["status"] == "environment-limited"
        for service in services
    )


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


def test_historical_evidence_provenance_is_not_treated_as_current_attestation() -> None:
    current = {item["id"]: item for item in evidence_freshness(as_of=date(2026, 9, 5))}
    assert current["live.vertical_slice"]["state"] == "unknown"
    assert current["live.vertical_slice"]["observed_at"] is None
    assert current["example.search_to_corpus"]["state"] == "not-applicable"


def test_ci_attestation_drives_freshness_without_rewriting_declarations() -> None:
    attestation = build_evidence_attestation(
        commit="a" * 40,
        run_url="https://github.com/example/repo/actions/runs/42",
        observed_at="2026-09-05T10:00:00Z",
    )
    fresh = {
        item["id"]: item
        for item in evidence_freshness(attestation=attestation, as_of=date(2026, 9, 10))
    }
    stale = {
        item["id"]: item
        for item in evidence_freshness(attestation=attestation, as_of=date(2026, 10, 1))
    }
    assert fresh["live.vertical_slice"]["state"] == "fresh"
    assert fresh["live.vertical_slice"]["age_days"] == 5
    assert fresh["live.vertical_slice"]["observed_at"] == "2026-09-05T10:00:00Z"
    assert stale["live.vertical_slice"]["state"] == "stale"
    assert stale["live.vertical_slice"]["age_days"] == 26


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

    schema = _reference_schema()
    properties = schema["properties"]
    required = schema["required"]
    assert isinstance(properties, dict)
    assert isinstance(required, list)
    assert properties["id"]["const"] == "gallica-sdk-reference"
    assert "operational_contracts_export" in required
    assert "observed_at" in properties["evidence"]["items"]["properties"]
    assert "freshness_days" in properties["evidence"]["items"]["properties"]

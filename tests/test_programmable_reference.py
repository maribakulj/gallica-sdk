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


def test_reference_schema_version_is_stable_v1() -> None:
    assert REFERENCE_SCHEMA_VERSION == "1.0"
    schema = json.loads(Path("reference/schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["id"]["const"] == "gallica-sdk-reference"

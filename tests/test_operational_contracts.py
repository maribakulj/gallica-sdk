from __future__ import annotations

import json

import pytest

from gallica import capabilities, operational_contract, operational_contracts


def test_operational_contracts_cover_every_capability_once() -> None:
    expected = [item["id"] for item in capabilities()]
    contracts = operational_contracts()
    actual = [item["id"] for item in contracts]

    assert actual == expected
    assert len(actual) == len(set(actual))


def test_every_contract_has_output_and_error_semantics() -> None:
    for contract in operational_contracts():
        assert contract["output_semantics"]
        assert contract["errors"]
        assert contract["returns"]
        assert isinstance(contract["services"], tuple)
        assert isinstance(contract["evidence"], tuple)
        assert isinstance(contract["freshness"], tuple)


def test_network_contracts_resolve_services_and_live_evidence() -> None:
    for contract in operational_contracts():
        if not contract["services"]:
            continue
        assert any(item["kind"] == "live-test" for item in contract["evidence"]), contract["id"]
        assert any(item["state"] in {"fresh", "stale"} for item in contract["freshness"]), contract["id"]


def test_resolved_page_alto_contract_is_self_contained() -> None:
    contract = operational_contract("page_alto")
    assert contract["call"] == "Page.alto"
    assert contract["source_media_type"] == "application/xml"
    assert {service["id"] for service in contract["services"]} == {"alto"}
    assert contract["evidence"]
    assert "ALTO" in contract["output_semantics"]


def test_contracts_are_json_serializable() -> None:
    json.dumps(operational_contracts())


def test_unknown_contract_id_is_explicit_error() -> None:
    with pytest.raises(KeyError, match="unknown capability"):
        operational_contract("does-not-exist")

from __future__ import annotations

import json

import pytest

from gallica import (
    build_evidence_attestation,
    capabilities,
    operational_contract,
    operational_contracts,
)


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


def test_network_contracts_are_unknown_without_current_attestation() -> None:
    for contract in operational_contracts():
        if not contract["services"]:
            continue
        assert any(item["kind"] == "live-test" for item in contract["evidence"]), contract["id"]
        assert any(item["state"] == "unknown" for item in contract["freshness"]), contract["id"]


def test_attestation_resolves_current_operational_freshness() -> None:
    attestation = build_evidence_attestation(
        commit="b" * 40,
        run_url="https://github.com/example/repo/actions/runs/99",
        observed_at="2026-09-05T10:00:00Z",
    )
    contract = operational_contract("page_alto", attestation=attestation)
    assert contract["freshness"]
    assert all(item["state"] == "fresh" for item in contract["freshness"])


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

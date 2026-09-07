from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from gallica import (
    build_evidence_attestation,
    evidence,
    evidence_freshness,
    load_evidence_attestation,
)
from gallica.evidence import (
    load_live_evidence_observations,
    record_live_evidence,
)


def _observations(*, limited: set[str] | None = None) -> tuple[dict[str, str], ...]:
    limited_ids = limited or set()
    return tuple(
        {
            "evidence_id": item["id"],
            "service_outcome": (
                "environment-limited" if item["id"] in limited_ids else "operational"
            ),
            "observed_at": "2026-09-05T12:00:00Z",
        }
        for item in evidence()
        if item["kind"] == "live-test"
    )


def test_evidence_declarations_do_not_embed_historical_observations() -> None:
    for item in evidence():
        assert "observed_at" not in item
        assert "observed_commit" not in item
        assert "observed_run" not in item


def test_attestation_covers_every_observed_declared_live_test() -> None:
    attestation = build_evidence_attestation(
        commit="c" * 40,
        run_url="https://github.com/example/repo/actions/runs/7",
        observations=_observations(limited={"live.search_categories"}),
        generated_at="2026-09-05T12:01:00Z",
    )
    declared = {item["id"] for item in evidence() if item["kind"] == "live-test"}
    attested = {item["evidence_id"] for item in attestation["records"]}
    assert attested == declared
    assert all(item["test_outcome"] == "passed" for item in attestation["records"])
    assert all(item["commit"] == "c" * 40 for item in attestation["records"])
    categories = next(
        item for item in attestation["records"] if item["evidence_id"] == "live.search_categories"
    )
    assert categories["service_outcome"] == "environment-limited"


def test_attestation_rejects_missing_live_observations() -> None:
    observations = _observations()
    with pytest.raises(ValueError, match="missing live evidence observations"):
        build_evidence_attestation(
            commit="c" * 40,
            run_url="https://github.com/example/repo/actions/runs/7",
            observations=observations[:-1],
        )


def test_live_observation_jsonl_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "live-results.jsonl"
    record_live_evidence(
        "live.search_categories",
        service_outcome="environment-limited",
        detail="Categories returned HTML from this runner",
        observed_at="2026-09-05T12:00:00Z",
        path=path,
    )
    loaded = load_live_evidence_observations(path)
    assert loaded == (
        {
            "evidence_id": "live.search_categories",
            "service_outcome": "environment-limited",
            "observed_at": "2026-09-05T12:00:00Z",
            "detail": "Categories returned HTML from this runner",
        },
    )


def test_attestation_round_trip(tmp_path: Path) -> None:
    attestation = build_evidence_attestation(
        commit="d" * 40,
        run_url="https://github.com/example/repo/actions/runs/8",
        observations=_observations(),
        generated_at="2026-09-05T12:01:00Z",
    )
    path = tmp_path / "attestation.json"
    path.write_text(json.dumps(attestation), encoding="utf-8")
    loaded = load_evidence_attestation(path)
    assert loaded == attestation


def test_legacy_v1_attestation_does_not_claim_service_operability(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_at": "2026-09-05T12:00:00Z",
                "commit": "e" * 40,
                "run_url": "https://github.com/example/repo/actions/runs/9",
                "records": [
                    {
                        "evidence_id": "live.vertical_slice",
                        "outcome": "passed",
                        "observed_at": "2026-09-05T12:00:00Z",
                        "commit": "e" * 40,
                        "run_url": "https://github.com/example/repo/actions/runs/9",
                        "confidence": "high",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_evidence_attestation(path)
    assert loaded["records"][0]["service_outcome"] == "unknown"
    freshness = {
        item["id"]: item
        for item in evidence_freshness(attestation=loaded, as_of=date(2026, 9, 6))
    }
    assert freshness["live.vertical_slice"]["state"] == "unknown"


def test_attestation_loader_rejects_record_provenance_mismatch(tmp_path: Path) -> None:
    attestation = build_evidence_attestation(
        commit="a" * 40,
        run_url="https://github.com/example/repo/actions/runs/10",
        observations=_observations(),
        generated_at="2026-09-05T12:01:00Z",
    )
    payload = json.loads(json.dumps(attestation))
    payload["records"][0]["commit"] = "b" * 40
    path = tmp_path / "mismatch.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="commit mismatch"):
        load_evidence_attestation(path)


def test_attestation_loader_rejects_invalid_v2_service_outcome(tmp_path: Path) -> None:
    attestation = build_evidence_attestation(
        commit="a" * 40,
        run_url="https://github.com/example/repo/actions/runs/11",
        observations=_observations(),
        generated_at="2026-09-05T12:01:00Z",
    )
    payload = json.loads(json.dumps(attestation))
    payload["records"][0]["service_outcome"] = "probably-fine"
    path = tmp_path / "invalid-outcome.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid service_outcome"):
        load_evidence_attestation(path)


def test_attestation_rejects_ambiguous_provenance() -> None:
    with pytest.raises(ValueError, match="40-character"):
        build_evidence_attestation(
            commit="short",
            run_url="https://github.com/example/run",
            observations=_observations(),
        )
    with pytest.raises(ValueError, match="40-character"):
        build_evidence_attestation(
            commit="g" * 40,
            run_url="https://github.com/example/run",
            observations=_observations(),
        )
    with pytest.raises(ValueError, match="https"):
        build_evidence_attestation(
            commit="e" * 40,
            run_url="not-a-url",
            observations=_observations(),
        )


def test_attestation_rejects_invalid_observation_timestamp() -> None:
    observations = list(_observations())
    observations[0]["observed_at"] = "not-a-timestamp"
    with pytest.raises(ValueError, match="ISO 8601"):
        build_evidence_attestation(
            commit="e" * 40,
            run_url="https://github.com/example/run",
            observations=tuple(observations),
        )

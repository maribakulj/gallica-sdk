from __future__ import annotations

import json
from pathlib import Path

import pytest

from gallica import (
    build_evidence_attestation,
    evidence,
    load_evidence_attestation,
)


def test_attestation_covers_every_declared_live_test() -> None:
    attestation = build_evidence_attestation(
        commit="c" * 40,
        run_url="https://github.com/example/repo/actions/runs/7",
        observed_at="2026-09-05T12:00:00Z",
    )
    declared = {item["id"] for item in evidence() if item["kind"] == "live-test"}
    attested = {item["evidence_id"] for item in attestation["records"]}
    assert attested == declared
    assert all(item["outcome"] == "passed" for item in attestation["records"])
    assert all(item["commit"] == "c" * 40 for item in attestation["records"])


def test_attestation_round_trip(tmp_path: Path) -> None:
    attestation = build_evidence_attestation(
        commit="d" * 40,
        run_url="https://github.com/example/repo/actions/runs/8",
        observed_at="2026-09-05T12:00:00Z",
    )
    path = tmp_path / "attestation.json"
    path.write_text(json.dumps(attestation), encoding="utf-8")
    loaded = load_evidence_attestation(path)
    assert loaded == attestation


def test_attestation_rejects_ambiguous_provenance() -> None:
    with pytest.raises(ValueError, match="40-character"):
        build_evidence_attestation(commit="short", run_url="https://github.com/example/run")
    with pytest.raises(ValueError, match="https"):
        build_evidence_attestation(commit="e" * 40, run_url="not-a-url")

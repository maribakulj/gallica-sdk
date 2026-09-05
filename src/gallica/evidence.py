from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TypedDict


class EvidenceSpec(TypedDict, total=False):
    id: str
    kind: str
    status: str
    target: str
    description: str
    observed_at: str
    observed_commit: str
    observed_run: str
    freshness_days: int
    confidence: str


class LiveObservation(TypedDict):
    observed_at: str
    observed_commit: str
    observed_run: str
    freshness_days: int
    confidence: str


class EvidenceAttestationRecord(TypedDict):
    evidence_id: str
    outcome: str
    observed_at: str
    commit: str
    run_url: str
    confidence: str


class EvidenceAttestation(TypedDict):
    schema_version: str
    generated_at: str
    commit: str
    run_url: str
    records: tuple[EvidenceAttestationRecord, ...]


class CapabilityEvidence(TypedDict):
    capability: str
    services: tuple[str, ...]
    evidence: tuple[str, ...]
    example: str | None


class EvidenceFreshness(TypedDict):
    id: str
    state: str
    age_days: int | None
    observed_at: str | None
    confidence: str | None


_LAST_LIVE_OBSERVATION: LiveObservation = {
    "observed_at": "2026-09-04T16:42:34Z",
    "observed_commit": "858dc473b9cd38cade788493f15ff9dde9e77985",
    "observed_run": "https://github.com/maribakulj/gallica-sdk/actions/runs/33896647794",
    "freshness_days": 14,
    "confidence": "high",
}


EVIDENCE: tuple[EvidenceSpec, ...] = (
    {"id": "live.vertical_slice", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_vertical_slice", "description": "Public smoke validation for SRU, Pagination, OAIRecord, ALTO and IIIF image access.", **_LAST_LIVE_OBSERVATION},
    {"id": "live.document_access", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_phase1_document_access", "description": "Public validation for ContentSearch, dated Issues resolution and safe texteBrut behavior, including explicit anti-bot challenge detection when cold runners are blocked.", **_LAST_LIVE_OBSERVATION},
    {"id": "live.corpus_document", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_corpus_v1", "description": "Public corpus validation for metadata artifacts, provenance-aware resume and manifest stability.", **_LAST_LIVE_OBSERVATION},
    {"id": "live.corpus_pages", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_corpus_page_artifacts", "description": "Public corpus validation for ALTO/image page artifacts and resume behavior.", **_LAST_LIVE_OBSERVATION},
    {"id": "live.search_pagination", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live_usability.py::test_public_search_all_paginates_and_exposes_arks", "description": "Public validation for lazy SRU pagination and search-result ARK handoff to Corpus.", **_LAST_LIVE_OBSERVATION},
    {"id": "example.search_to_corpus", "kind": "example", "status": "checked-in", "target": "examples/search_to_corpus.py", "description": "Minimal search-to-corpus workflow intended for humans and coding agents.", "confidence": "reference"},
)


CAPABILITY_EVIDENCE: tuple[CapabilityEvidence, ...] = (
    {"capability": "document", "services": (), "evidence": (), "example": None},
    {"capability": "periodical", "services": (), "evidence": (), "example": None},
    {"capability": "corpus", "services": (), "evidence": ("live.search_pagination",), "example": "example.search_to_corpus"},
    {"capability": "search", "services": ("sru",), "evidence": ("live.vertical_slice",), "example": "example.search_to_corpus"},
    {"capability": "search_all", "services": ("sru",), "evidence": ("live.search_pagination",), "example": "example.search_to_corpus"},
    {"capability": "document_metadata", "services": ("oai-record",), "evidence": ("live.vertical_slice", "live.corpus_document"), "example": None},
    {"capability": "document_page_count", "services": ("pagination",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "document_text", "services": ("text",), "evidence": ("live.document_access",), "example": None},
    {"capability": "content_search", "services": ("content-search",), "evidence": ("live.document_access",), "example": None},
    {"capability": "page_text", "services": ("text",), "evidence": ("live.document_access",), "example": None},
    {"capability": "page_alto", "services": ("alto",), "evidence": ("live.vertical_slice", "live.corpus_pages"), "example": None},
    {"capability": "page_iiif_info", "services": ("iiif-image",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "page_image", "services": ("iiif-image",), "evidence": ("live.vertical_slice", "live.corpus_pages"), "example": None},
    {"capability": "periodical_issue", "services": ("issues",), "evidence": ("live.document_access",), "example": None},
    {"capability": "corpus_fetch", "services": ("oai-record", "text", "alto", "iiif-image"), "evidence": ("live.corpus_document", "live.corpus_pages", "live.document_access"), "example": "example.search_to_corpus"},
)


def evidence() -> tuple[EvidenceSpec, ...]:
    return EVIDENCE


def capability_evidence() -> tuple[CapabilityEvidence, ...]:
    return CAPABILITY_EVIDENCE


def build_evidence_attestation(
    *,
    commit: str,
    run_url: str,
    observed_at: str | None = None,
) -> EvidenceAttestation:
    """Build an attestation after the complete live-test suite has passed."""
    if len(commit) != 40:
        raise ValueError("commit must be a full 40-character SHA")
    if not run_url.startswith("https://"):
        raise ValueError("run_url must be an https URL")
    timestamp = observed_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    records = tuple(
        EvidenceAttestationRecord(
            evidence_id=item["id"],
            outcome="passed",
            observed_at=timestamp,
            commit=commit,
            run_url=run_url,
            confidence=item.get("confidence", "high"),
        )
        for item in EVIDENCE
        if item["kind"] == "live-test"
    )
    return {
        "schema_version": "1.0",
        "generated_at": timestamp,
        "commit": commit,
        "run_url": run_url,
        "records": records,
    }


def load_evidence_attestation(path: str | Path) -> EvidenceAttestation:
    """Load and minimally validate a CI-generated evidence attestation."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported evidence attestation schema")
    records_raw = payload.get("records")
    if not isinstance(records_raw, list):
        raise TypeError("attestation records must be a list")
    records: list[EvidenceAttestationRecord] = []
    for raw in records_raw:
        if not isinstance(raw, dict):
            raise TypeError("attestation record must be an object")
        records.append(
            {
                "evidence_id": str(raw["evidence_id"]),
                "outcome": str(raw["outcome"]),
                "observed_at": str(raw["observed_at"]),
                "commit": str(raw["commit"]),
                "run_url": str(raw["run_url"]),
                "confidence": str(raw["confidence"]),
            }
        )
    return {
        "schema_version": "1.0",
        "generated_at": str(payload["generated_at"]),
        "commit": str(payload["commit"]),
        "run_url": str(payload["run_url"]),
        "records": tuple(records),
    }


def evidence_freshness(
    *,
    attestation: EvidenceAttestation | None = None,
    as_of: date | None = None,
) -> tuple[EvidenceFreshness, ...]:
    """Classify live evidence from an explicit CI attestation.

    Historical observation fields embedded in evidence declarations are retained for
    backwards compatibility, but are deliberately not treated as current freshness.
    Without an attestation, live evidence is therefore ``unknown``.
    """
    today = as_of or datetime.now(UTC).date()
    attested = {
        record["evidence_id"]: record
        for record in (attestation["records"] if attestation is not None else ())
    }
    result: list[EvidenceFreshness] = []
    for item in EVIDENCE:
        confidence = item.get("confidence")
        if item["kind"] != "live-test":
            result.append({"id": item["id"], "state": "not-applicable", "age_days": None, "observed_at": None, "confidence": confidence})
            continue
        record = attested.get(item["id"])
        if record is None:
            result.append({"id": item["id"], "state": "unknown", "age_days": None, "observed_at": None, "confidence": confidence})
            continue
        observed_at = record["observed_at"]
        observed_date = datetime.fromisoformat(observed_at).date()
        age_days = (today - observed_date).days
        threshold = item.get("freshness_days", 14)
        state = "fresh" if age_days <= threshold else "stale"
        if record["outcome"] != "passed":
            state = "failed"
        result.append({"id": item["id"], "state": state, "age_days": age_days, "observed_at": observed_at, "confidence": record["confidence"]})
    return tuple(result)

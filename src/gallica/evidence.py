from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import NotRequired, TypedDict


class EvidenceSpec(TypedDict, total=False):
    id: str
    kind: str
    status: str
    target: str
    description: str
    freshness_days: int
    confidence: str


class LiveEvidenceObservation(TypedDict):
    evidence_id: str
    service_outcome: str
    observed_at: str
    detail: NotRequired[str]


class EvidenceAttestationRecord(TypedDict):
    evidence_id: str
    test_outcome: str
    service_outcome: str
    observed_at: str
    commit: str
    run_url: str
    confidence: str
    detail: NotRequired[str]


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
    test_outcome: str | None
    service_outcome: str | None


_LIVE_EVIDENCE_ENV = "GALLICA_LIVE_EVIDENCE_PATH"
_SERVICE_OUTCOMES = frozenset({"operational", "environment-limited"})


EVIDENCE: tuple[EvidenceSpec, ...] = (
    {"id": "live.vertical_slice", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_vertical_slice", "description": "Public smoke validation for SRU, structured Pagination, Toc, OAIRecord, ALTO and IIIF image access.", "freshness_days": 14, "confidence": "high"},
    {"id": "live.document_access", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_phase1_document_access", "description": "Public validation for ContentSearch excerpts/geometry/pagination and dated Issues resolution.", "freshness_days": 14, "confidence": "high"},
    {"id": "live.text_access", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_phase1_document_access", "description": "Public validation for plain OCR texteBrut behavior, including explicit anti-bot challenge detection when cold runners are blocked.", "freshness_days": 14, "confidence": "high"},
    {"id": "live.corpus_document", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_corpus_v1", "description": "Public corpus validation for metadata artifacts, provenance-aware resume and manifest stability.", "freshness_days": 14, "confidence": "high"},
    {"id": "live.corpus_pages", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live.py::test_public_gallica_corpus_page_artifacts", "description": "Public corpus validation for ALTO/image page artifacts and resume behavior.", "freshness_days": 14, "confidence": "high"},
    {"id": "live.search_pagination", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live_usability.py::test_public_search_all_paginates_and_exposes_arks", "description": "Public validation for lazy SRU pagination and search-result ARK handoff to Corpus.", "freshness_days": 14, "confidence": "high"},
    {"id": "live.search_categories", "kind": "live-test", "status": "passing-in-ci", "target": "tests/test_live_usability.py::test_public_categories_exposes_search_refinements", "description": "Public validation for Categories search refinements, approximate counts and API-category to CQL-field mappings.", "freshness_days": 14, "confidence": "high"},
    {"id": "example.search_to_corpus", "kind": "example", "status": "checked-in", "target": "examples/search_to_corpus.py", "description": "Minimal search-to-corpus workflow intended for humans and coding agents.", "confidence": "reference"},
)


CAPABILITY_EVIDENCE: tuple[CapabilityEvidence, ...] = (
    {"capability": "document", "services": (), "evidence": (), "example": None},
    {"capability": "periodical", "services": (), "evidence": (), "example": None},
    {"capability": "corpus", "services": (), "evidence": ("live.search_pagination",), "example": "example.search_to_corpus"},
    {"capability": "search", "services": ("sru",), "evidence": ("live.vertical_slice",), "example": "example.search_to_corpus"},
    {"capability": "categories", "services": ("categories",), "evidence": ("live.search_categories",), "example": None},
    {"capability": "search_all", "services": ("sru",), "evidence": ("live.search_pagination",), "example": "example.search_to_corpus"},
    {"capability": "document_metadata", "services": ("oai-record",), "evidence": ("live.vertical_slice", "live.corpus_document"), "example": None},
    {"capability": "document_pagination", "services": ("pagination",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "document_page_count", "services": ("pagination",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "document_toc", "services": ("toc",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "document_text", "services": ("text",), "evidence": ("live.text_access",), "example": None},
    {"capability": "content_search", "services": ("content-search",), "evidence": ("live.document_access",), "example": None},
    {"capability": "content_search_all", "services": ("content-search",), "evidence": ("live.document_access",), "example": None},
    {"capability": "page_text", "services": ("text",), "evidence": ("live.text_access",), "example": None},
    {"capability": "page_alto", "services": ("alto",), "evidence": ("live.vertical_slice", "live.corpus_pages"), "example": None},
    {"capability": "page_iiif_info", "services": ("iiif-image",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "page_image", "services": ("iiif-image",), "evidence": ("live.vertical_slice", "live.corpus_pages"), "example": None},
    {"capability": "periodical_issue", "services": ("issues",), "evidence": ("live.document_access",), "example": None},
    {"capability": "corpus_fetch", "services": ("oai-record", "text", "alto", "iiif-image"), "evidence": ("live.corpus_document", "live.corpus_pages", "live.text_access"), "example": "example.search_to_corpus"},
)


def evidence() -> tuple[EvidenceSpec, ...]:
    return EVIDENCE


def capability_evidence() -> tuple[CapabilityEvidence, ...]:
    return CAPABILITY_EVIDENCE


def _declared_live_evidence() -> dict[str, EvidenceSpec]:
    return {item["id"]: item for item in EVIDENCE if item["kind"] == "live-test"}


def record_live_evidence(
    evidence_id: str,
    *,
    service_outcome: str,
    detail: str | None = None,
    observed_at: str | None = None,
    path: str | Path | None = None,
) -> None:
    declared = _declared_live_evidence()
    if evidence_id not in declared:
        raise KeyError(f"unknown live evidence id: {evidence_id}")
    if service_outcome not in _SERVICE_OUTCOMES:
        allowed = ", ".join(sorted(_SERVICE_OUTCOMES))
        raise ValueError(f"service_outcome must be one of: {allowed}")

    target = Path(path) if path is not None else None
    if target is None:
        env_path = os.environ.get(_LIVE_EVIDENCE_ENV)
        if not env_path:
            return
        target = Path(env_path)

    timestamp = observed_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    record: LiveEvidenceObservation = {
        "evidence_id": evidence_id,
        "service_outcome": service_outcome,
        "observed_at": timestamp,
    }
    if detail:
        record["detail"] = detail

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_live_evidence_observations(path: str | Path) -> tuple[LiveEvidenceObservation, ...]:
    records: list[LiveEvidenceObservation] = []
    seen: set[str] = set()
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise TypeError(f"live evidence line {line_number} must be an object")
        evidence_id = str(raw["evidence_id"])
        if evidence_id in seen:
            raise ValueError(f"duplicate live evidence observation: {evidence_id}")
        if evidence_id not in _declared_live_evidence():
            raise ValueError(f"undeclared live evidence observation: {evidence_id}")
        service_outcome = str(raw["service_outcome"])
        if service_outcome not in _SERVICE_OUTCOMES:
            raise ValueError(f"invalid service_outcome for {evidence_id}: {service_outcome}")
        observed_at = str(raw["observed_at"])
        datetime.fromisoformat(observed_at)
        record: LiveEvidenceObservation = {
            "evidence_id": evidence_id,
            "service_outcome": service_outcome,
            "observed_at": observed_at,
        }
        detail = raw.get("detail")
        if detail is not None:
            record["detail"] = str(detail)
        records.append(record)
        seen.add(evidence_id)
    return tuple(records)


def build_evidence_attestation(
    *,
    commit: str,
    run_url: str,
    observations: tuple[LiveEvidenceObservation, ...],
    generated_at: str | None = None,
) -> EvidenceAttestation:
    if len(commit) != 40:
        raise ValueError("commit must be a full 40-character SHA")
    if not run_url.startswith("https://"):
        raise ValueError("run_url must be an https URL")

    declared = _declared_live_evidence()
    observed: dict[str, LiveEvidenceObservation] = {}
    for observation in observations:
        evidence_id = observation["evidence_id"]
        if evidence_id in observed:
            raise ValueError(f"duplicate live evidence observation: {evidence_id}")
        if evidence_id not in declared:
            raise ValueError(f"undeclared live evidence observation: {evidence_id}")
        service_outcome = observation["service_outcome"]
        if service_outcome not in _SERVICE_OUTCOMES:
            raise ValueError(f"invalid service_outcome for {evidence_id}: {service_outcome}")
        datetime.fromisoformat(observation["observed_at"])
        observed[evidence_id] = observation

    missing = set(declared) - set(observed)
    if missing:
        raise ValueError(f"missing live evidence observations: {', '.join(sorted(missing))}")

    timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    records: list[EvidenceAttestationRecord] = []
    for item in EVIDENCE:
        if item["kind"] != "live-test":
            continue
        observation = observed[item["id"]]
        record: EvidenceAttestationRecord = {
            "evidence_id": item["id"],
            "test_outcome": "passed",
            "service_outcome": observation["service_outcome"],
            "observed_at": observation["observed_at"],
            "commit": commit,
            "run_url": run_url,
            "confidence": item.get("confidence", "high"),
        }
        detail = observation.get("detail")
        if detail:
            record["detail"] = detail
        records.append(record)
    return {
        "schema_version": "2.0",
        "generated_at": timestamp,
        "commit": commit,
        "run_url": run_url,
        "records": tuple(records),
    }


def load_evidence_attestation(path: str | Path) -> EvidenceAttestation:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    schema_version = str(payload.get("schema_version", ""))
    if schema_version not in {"1.0", "2.0"}:
        raise ValueError("unsupported evidence attestation schema")
    records_raw = payload.get("records")
    if not isinstance(records_raw, list):
        raise TypeError("attestation records must be a list")
    records: list[EvidenceAttestationRecord] = []
    for raw in records_raw:
        if not isinstance(raw, dict):
            raise TypeError("attestation record must be an object")
        if schema_version == "1.0":
            test_outcome = str(raw["outcome"])
            service_outcome = "unknown"
        else:
            test_outcome = str(raw["test_outcome"])
            service_outcome = str(raw["service_outcome"])
        record: EvidenceAttestationRecord = {
            "evidence_id": str(raw["evidence_id"]),
            "test_outcome": test_outcome,
            "service_outcome": service_outcome,
            "observed_at": str(raw["observed_at"]),
            "commit": str(raw["commit"]),
            "run_url": str(raw["run_url"]),
            "confidence": str(raw["confidence"]),
        }
        detail = raw.get("detail")
        if detail is not None:
            record["detail"] = str(detail)
        records.append(record)
    return {
        "schema_version": schema_version,
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
    today = as_of or datetime.now(UTC).date()
    attested = {
        record["evidence_id"]: record
        for record in (attestation["records"] if attestation is not None else ())
    }
    result: list[EvidenceFreshness] = []
    for item in EVIDENCE:
        confidence = item.get("confidence")
        if item["kind"] != "live-test":
            result.append({"id": item["id"], "state": "not-applicable", "age_days": None, "observed_at": None, "confidence": confidence, "test_outcome": None, "service_outcome": None})
            continue
        record = attested.get(item["id"])
        if record is None:
            result.append({"id": item["id"], "state": "unknown", "age_days": None, "observed_at": None, "confidence": confidence, "test_outcome": None, "service_outcome": None})
            continue
        observed_at = record["observed_at"]
        observed_date = datetime.fromisoformat(observed_at).date()
        age_days = (today - observed_date).days
        threshold = item.get("freshness_days", 14)
        if record["test_outcome"] != "passed" or record["service_outcome"] == "unknown":
            state = "failed" if record["test_outcome"] != "passed" else "unknown"
        else:
            state = "fresh" if age_days <= threshold else "stale"
        result.append({"id": item["id"], "state": state, "age_days": age_days, "observed_at": observed_at, "confidence": record["confidence"], "test_outcome": record["test_outcome"], "service_outcome": record["service_outcome"]})
    return tuple(result)

from __future__ import annotations

from datetime import date, datetime, timezone
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


_LAST_LIVE_OBSERVATION = {
    "observed_at": "2026-09-04T16:42:34Z",
    "observed_commit": "858dc473b9cd38cade788493f15ff9dde9e77985",
    "observed_run": "https://github.com/maribakulj/gallica-sdk/actions/runs/33896647794",
    "freshness_days": 14,
    "confidence": "high",
}


EVIDENCE: tuple[EvidenceSpec, ...] = (
    {
        "id": "live.vertical_slice",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_vertical_slice",
        "description": "Public smoke validation for SRU, Pagination, OAIRecord, ALTO and IIIF image access.",
        **_LAST_LIVE_OBSERVATION,
    },
    {
        "id": "live.document_access",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_phase1_document_access",
        "description": "Public smoke validation for document/page text, ContentSearch and dated Issues resolution.",
        **_LAST_LIVE_OBSERVATION,
    },
    {
        "id": "live.corpus_document",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_corpus_v1",
        "description": "Public corpus validation for metadata/text artifacts, resume and manifest stability.",
        **_LAST_LIVE_OBSERVATION,
    },
    {
        "id": "live.corpus_pages",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_corpus_page_artifacts",
        "description": "Public corpus validation for ALTO/image page artifacts and resume behavior.",
        **_LAST_LIVE_OBSERVATION,
    },
    {
        "id": "live.search_pagination",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live_usability.py::test_public_search_all_paginates_and_exposes_arks",
        "description": "Public validation for lazy SRU pagination and search-result ARK handoff to Corpus.",
        **_LAST_LIVE_OBSERVATION,
    },
    {
        "id": "example.search_to_corpus",
        "kind": "example",
        "status": "checked-in",
        "target": "examples/search_to_corpus.py",
        "description": "Minimal search-to-corpus workflow intended for humans and coding agents.",
        "confidence": "reference",
    },
)


CAPABILITY_EVIDENCE: tuple[CapabilityEvidence, ...] = (
    {"capability": "document", "services": (), "evidence": (), "example": None},
    {"capability": "periodical", "services": (), "evidence": (), "example": None},
    {"capability": "corpus", "services": (), "evidence": ("live.search_pagination",), "example": "example.search_to_corpus"},
    {"capability": "search", "services": ("sru",), "evidence": ("live.vertical_slice",), "example": "example.search_to_corpus"},
    {"capability": "search_all", "services": ("sru",), "evidence": ("live.search_pagination",), "example": "example.search_to_corpus"},
    {"capability": "document_metadata", "services": ("oai-record",), "evidence": ("live.vertical_slice", "live.corpus_document"), "example": None},
    {"capability": "document_page_count", "services": ("pagination",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "document_text", "services": ("text",), "evidence": ("live.document_access", "live.corpus_document"), "example": None},
    {"capability": "content_search", "services": ("content-search",), "evidence": ("live.document_access",), "example": None},
    {"capability": "page_text", "services": ("text",), "evidence": ("live.document_access",), "example": None},
    {"capability": "page_alto", "services": ("alto",), "evidence": ("live.vertical_slice", "live.corpus_pages"), "example": None},
    {"capability": "page_iiif_info", "services": ("iiif-image",), "evidence": ("live.vertical_slice",), "example": None},
    {"capability": "page_image", "services": ("iiif-image",), "evidence": ("live.vertical_slice", "live.corpus_pages"), "example": None},
    {"capability": "periodical_issue", "services": ("issues",), "evidence": ("live.document_access",), "example": None},
    {"capability": "corpus_fetch", "services": ("oai-record", "text", "alto", "iiif-image"), "evidence": ("live.corpus_document", "live.corpus_pages"), "example": "example.search_to_corpus"},
)


def evidence() -> tuple[EvidenceSpec, ...]:
    return EVIDENCE


def capability_evidence() -> tuple[CapabilityEvidence, ...]:
    return CAPABILITY_EVIDENCE


def evidence_freshness(*, as_of: date | None = None) -> tuple[EvidenceFreshness, ...]:
    """Classify live evidence as fresh/stale relative to its observation timestamp."""
    today = as_of or datetime.now(timezone.utc).date()
    result: list[EvidenceFreshness] = []
    for item in EVIDENCE:
        observed_at = item.get("observed_at")
        confidence = item.get("confidence")
        if item["kind"] != "live-test":
            result.append(
                {
                    "id": item["id"],
                    "state": "not-applicable",
                    "age_days": None,
                    "observed_at": observed_at,
                    "confidence": confidence,
                }
            )
            continue
        if observed_at is None:
            result.append(
                {
                    "id": item["id"],
                    "state": "unknown",
                    "age_days": None,
                    "observed_at": None,
                    "confidence": confidence,
                }
            )
            continue
        observed_date = datetime.fromisoformat(observed_at.replace("Z", "+00:00")).date()
        age_days = (today - observed_date).days
        threshold = item.get("freshness_days", 14)
        result.append(
            {
                "id": item["id"],
                "state": "fresh" if age_days <= threshold else "stale",
                "age_days": age_days,
                "observed_at": observed_at,
                "confidence": confidence,
            }
        )
    return tuple(result)

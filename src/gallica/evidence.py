from __future__ import annotations

from typing import TypedDict


class EvidenceSpec(TypedDict):
    id: str
    kind: str
    status: str
    target: str
    description: str


class CapabilityEvidence(TypedDict):
    capability: str
    services: tuple[str, ...]
    evidence: tuple[str, ...]
    example: str | None


EVIDENCE: tuple[EvidenceSpec, ...] = (
    {
        "id": "live.vertical_slice",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_vertical_slice",
        "description": "Public smoke validation for SRU, Pagination, OAIRecord, ALTO and IIIF image access.",
    },
    {
        "id": "live.document_access",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_phase1_document_access",
        "description": "Public smoke validation for document/page text, ContentSearch and dated Issues resolution.",
    },
    {
        "id": "live.corpus_document",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_corpus_v1",
        "description": "Public corpus validation for metadata/text artifacts, resume and manifest stability.",
    },
    {
        "id": "live.corpus_pages",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live.py::test_public_gallica_corpus_page_artifacts",
        "description": "Public corpus validation for ALTO/image page artifacts and resume behavior.",
    },
    {
        "id": "live.search_pagination",
        "kind": "live-test",
        "status": "passing-in-ci",
        "target": "tests/test_live_usability.py::test_public_search_all_paginates_and_exposes_arks",
        "description": "Public validation for lazy SRU pagination and search-result ARK handoff to Corpus.",
    },
    {
        "id": "example.search_to_corpus",
        "kind": "example",
        "status": "checked-in",
        "target": "examples/search_to_corpus.py",
        "description": "Minimal search-to-corpus workflow intended for humans and coding agents.",
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

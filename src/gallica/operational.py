from __future__ import annotations

from typing import TypedDict

from .agent import CapabilitySpec, capabilities
from .evidence import EvidenceFreshness, EvidenceSpec, capability_evidence, evidence, evidence_freshness
from .reference import ServiceSpec, SERVICES


class OperationalSemantics(TypedDict):
    source_media_type: str | None
    output_semantics: str
    errors: tuple[str, ...]


class OperationalContract(TypedDict):
    id: str
    call: str
    description: str
    parameters: tuple[dict[str, object], ...]
    returns: str
    constraints: tuple[str, ...]
    source_media_type: str | None
    output_semantics: str
    errors: tuple[str, ...]
    services: tuple[ServiceSpec, ...]
    evidence: tuple[EvidenceSpec, ...]
    freshness: tuple[EvidenceFreshness, ...]
    example: EvidenceSpec | None


_SEMANTICS: dict[str, OperationalSemantics] = {
    "document": {
        "source_media_type": None,
        "output_semantics": "Local normalized Document handle; no network request is made.",
        "errors": ("Invalid or empty ARK input raises ValueError during normalization.",),
    },
    "periodical": {
        "source_media_type": None,
        "output_semantics": "Local Periodical handle; network access occurs only on issue resolution.",
        "errors": ("Invalid or empty ARK input raises ValueError during normalization.",),
    },
    "corpus": {
        "source_media_type": None,
        "output_semantics": "Ordered, normalized and deduplicated Corpus handle; no network request is made.",
        "errors": ("Invalid ARK input raises ValueError during corpus construction.",),
    },
    "search": {
        "source_media_type": "application/xml",
        "output_semantics": "One SRU page parsed into SearchResults while preserving raw_xml.",
        "errors": (
            "maximum_records outside 1..50 raises ValueError before the request.",
            "Unrecoverable HTTP responses propagate as httpx HTTP errors after bounded retries.",
        ),
    },
    "search_all": {
        "source_media_type": "application/xml",
        "output_semantics": "Lazy iterator of DublinCoreRecord values fetched one SRU page at a time.",
        "errors": (
            "page_size outside 1..50 or a non-positive limit raises ValueError.",
            "Network failures may occur during iteration because pages are fetched lazily.",
        ),
    },
    "document_metadata": {
        "source_media_type": "application/xml",
        "output_semantics": "DocumentMetadata with repeatable Dublin Core fields, Gallica technical fields and raw_xml.",
        "errors": ("Unrecoverable HTTP or malformed XML failures propagate to the caller.",),
    },
    "document_page_count": {
        "source_media_type": "application/xml",
        "output_semantics": "Integer image-view count parsed from Pagination nbVueImages.",
        "errors": ("Missing or unparsable nbVueImages raises a parsing error rather than returning a guessed count.",),
    },
    "document_text": {
        "source_media_type": "text/plain",
        "output_semantics": "Plain OCR text for the document representation.",
        "errors": ("Unrecoverable HTTP errors propagate after throttling and bounded retries.",),
    },
    "content_search": {
        "source_media_type": "application/xml",
        "output_semantics": "Typed ContentSearchResults with items, total count and raw_xml.",
        "errors": (
            "page and start_result must be positive when supplied.",
            "Unrecoverable HTTP or malformed XML failures propagate to the caller.",
        ),
    },
    "page_text": {
        "source_media_type": "text/plain",
        "output_semantics": "Plain OCR text for exactly one 1-based view.",
        "errors": ("Invalid page/view values are rejected; HTTP failures propagate after retries.",),
    },
    "page_alto": {
        "source_media_type": "application/xml",
        "output_semantics": "Raw ALTO XML bytes for one 1-based view; the SDK does not impose an incomplete ALTO object model.",
        "errors": ("Invalid view values are rejected; HTTP failures propagate after retries.",),
    },
    "page_iiif_info": {
        "source_media_type": "application/json",
        "output_semantics": "Decoded IIIF Image info.json mapping for one view.",
        "errors": ("HTTP failures or invalid JSON propagate rather than becoming an empty mapping.",),
    },
    "page_image": {
        "source_media_type": "image/*",
        "output_semantics": "Raw image bytes for one IIIF Image request using the requested width and format.",
        "errors": (
            "width below 1 raises ValueError.",
            "Unrecoverable HTTP errors propagate after the appropriate standard or HD rate bucket.",
        ),
    },
    "periodical_issue": {
        "source_media_type": "application/xml",
        "output_semantics": "Document handle for the exact dated issue, or None when Issues resolves no matching issue.",
        "errors": ("Network or malformed XML failures propagate; absence of a matching issue is represented by None.",),
    },
    "corpus_fetch": {
        "source_media_type": "multiple",
        "output_semantics": "CorpusReport plus explicit files and append-only manifest entries for attempts actually executed.",
        "errors": (
            "At least one artifact must be requested.",
            "ALTO/images require explicit positive views and image_width must be positive.",
            "Ordinary per-ARK failures are captured in CorpusReport and do not stop later ARKs.",
            "System-level interruptions are not swallowed.",
        ),
    },
}


def _parameter_dicts(spec: CapabilitySpec) -> tuple[dict[str, object], ...]:
    return tuple(dict(parameter) for parameter in spec["parameters"])


def operational_contracts() -> tuple[OperationalContract, ...]:
    """Resolve capabilities, services, evidence and freshness into one agent-facing contract."""
    services_by_id = {service["id"]: service for service in SERVICES}
    evidence_by_id = {item["id"]: item for item in evidence()}
    freshness_by_id = {item["id"]: item for item in evidence_freshness()}
    links_by_capability = {item["capability"]: item for item in capability_evidence()}

    result: list[OperationalContract] = []
    for spec in capabilities():
        capability_id = spec["id"]
        semantics = _SEMANTICS[capability_id]
        links = links_by_capability[capability_id]
        linked_evidence = tuple(evidence_by_id[item_id] for item_id in links["evidence"])
        linked_freshness = tuple(
            freshness_by_id[item_id]
            for item_id in links["evidence"]
            if item_id in freshness_by_id
        )
        example_id = links["example"]
        example = evidence_by_id[example_id] if example_id is not None else None
        result.append(
            {
                "id": capability_id,
                "call": spec["call"],
                "description": spec["description"],
                "parameters": _parameter_dicts(spec),
                "returns": spec["returns"],
                "constraints": spec["constraints"],
                "source_media_type": semantics["source_media_type"],
                "output_semantics": semantics["output_semantics"],
                "errors": semantics["errors"],
                "services": tuple(services_by_id[item_id] for item_id in links["services"]),
                "evidence": linked_evidence,
                "freshness": linked_freshness,
                "example": example,
            }
        )
    return tuple(result)


def operational_contract(capability_id: str) -> OperationalContract:
    """Return one fully resolved capability contract by stable capability ID."""
    for contract in operational_contracts():
        if contract["id"] == capability_id:
            return contract
    raise KeyError(f"unknown capability: {capability_id}")

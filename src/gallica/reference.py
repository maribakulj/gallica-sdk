from __future__ import annotations

from typing import TypedDict

from .agent import capabilities
from .evidence import CapabilityEvidence, EvidenceSpec, capability_evidence, evidence

REFERENCE_SCHEMA_VERSION = "1.2"
REFERENCE_ID = "gallica-sdk-reference"


class ServiceSpec(TypedDict):
    id: str
    name: str
    kind: str
    status: str
    base_url: str
    documentation: tuple[str, ...]
    notes: tuple[str, ...]


class CapabilityIndexSpec(TypedDict):
    id: str
    call: str


class ReferenceSpec(TypedDict):
    id: str
    schema_version: str
    purpose: str
    implementation: str
    authority: str
    capabilities_export: str
    services: tuple[ServiceSpec, ...]
    capability_index: tuple[CapabilityIndexSpec, ...]
    evidence: tuple[EvidenceSpec, ...]
    capability_evidence: tuple[CapabilityEvidence, ...]
    invariants: tuple[str, ...]


SERVICES: tuple[ServiceSpec, ...] = (
    {"id": "sru", "name": "Gallica SRU 1.2", "kind": "search", "status": "live-validated", "base_url": "https://gallica.bnf.fr/SRU", "documentation": ("https://api.bnf.fr/",), "notes": ("maximumRecords is capped at 50 by the SDK",)},
    {"id": "oai-record", "name": "Gallica OAIRecord", "kind": "metadata", "status": "live-validated", "base_url": "https://gallica.bnf.fr/services/OAIRecord", "documentation": ("https://api.bnf.fr/",), "notes": ("Dublin Core values may repeat",)},
    {"id": "pagination", "name": "Gallica Pagination", "kind": "structure", "status": "live-validated", "base_url": "https://gallica.bnf.fr/services/Pagination", "documentation": ("https://api.bnf.fr/",), "notes": ("nbVueImages is used as the image-view count",)},
    {"id": "issues", "name": "Gallica Issues", "kind": "periodicals", "status": "live-validated", "base_url": "https://gallica.bnf.fr/services/Issues", "documentation": ("https://api.bnf.fr/",), "notes": ("dated issue resolution uses dayOfYear",)},
    {"id": "content-search", "name": "Gallica ContentSearch", "kind": "ocr-search", "status": "live-validated", "base_url": "https://gallica.bnf.fr/services/ContentSearch", "documentation": ("https://api.bnf.fr/",), "notes": ("startResult is 1-based when supplied",)},
    {"id": "text", "name": "Gallica plain OCR text", "kind": "ocr", "status": "live-validated", "base_url": "https://gallica.bnf.fr/ark:/12148/", "documentation": ("https://api.bnf.fr/fr/node/232",), "notes": ("public quota documented as 5 requests/minute",)},
    {"id": "alto", "name": "Gallica ALTO", "kind": "ocr", "status": "live-validated", "base_url": "https://gallica.bnf.fr/RequestDigitalElement", "documentation": ("https://api.bnf.fr/",), "notes": ("views are 1-based",)},
    {"id": "iiif-image", "name": "Gallica IIIF Image", "kind": "image", "status": "live-validated", "base_url": "https://gallica.bnf.fr/iiif/", "documentation": ("https://api.bnf.fr/", "https://api.bnf.fr/fr/node/232"), "notes": ("1000px is the conservative SDK default", "width above 1000px is handled as high definition")},
    {"id": "pdf", "name": "Gallica PDF representation", "kind": "document", "status": "not-supported", "base_url": "https://gallica.bnf.fr/ark:/12148/", "documentation": ("https://api.bnf.fr/fr/node/232",), "notes": ("historical automated URL forms returned HTML in public CI validation", "the SDK intentionally exposes no pdf() method")},
)


def programmable_reference() -> ReferenceSpec:
    """Return the canonical discovery manifest with validation provenance."""
    return {
        "id": REFERENCE_ID,
        "schema_version": REFERENCE_SCHEMA_VERSION,
        "purpose": "Verified operational knowledge for humans, notebooks, pipelines and agents using public Gallica services.",
        "implementation": "gallica-sdk",
        "authority": "This project is an independent reference layer; BnF public documentation and live services remain authoritative.",
        "capabilities_export": "python scripts/export_capabilities.py",
        "services": SERVICES,
        "capability_index": tuple({"id": spec["id"], "call": spec["call"]} for spec in capabilities()),
        "evidence": evidence(),
        "capability_evidence": capability_evidence(),
        "invariants": (
            "A network capability is not marked supported without a relevant public live test.",
            "Every live-test evidence record carries an observation timestamp, tested commit and CI run.",
            "Evidence freshness is evaluated separately from support status and can become stale without changing the historical observation.",
            "Every service/evidence reference in capability_evidence must resolve in this manifest.",
            "Every public capability must have exactly one capability_evidence record.",
            "Raw XML remains available when the SDK exposes a structured XML-derived model.",
            "Corpus page downloads never imply all pages; views must be explicit.",
            "Rate-limit behavior is centralized in the shared transport.",
            "The checked-in JSON reference must exactly match this canonical Python representation.",
        ),
    }

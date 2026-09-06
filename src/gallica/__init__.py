from ._version import __version__
from .agent import CapabilitySpec, capabilities
from .client import Gallica
from .corpus import (
    Corpus,
    CorpusArtifactFailure,
    CorpusArtifactRecord,
    CorpusItemResult,
    CorpusReport,
)
from .document import Document, Page
from .evidence import (
    CapabilityEvidence,
    EvidenceAttestation,
    EvidenceAttestationRecord,
    EvidenceFreshness,
    EvidenceSpec,
    build_evidence_attestation,
    capability_evidence,
    evidence,
    evidence_freshness,
    load_evidence_attestation,
)
from .exceptions import GallicaError, GallicaResponseError
from .models import (
    CATEGORY_CQL_FIELDS,
    Categories,
    CategoryValue,
    ContentSearchItem,
    ContentSearchMatch,
    ContentSearchResults,
    DocumentMetadata,
    DublinCoreRecord,
    Pagination,
    PaginationPage,
    SearchResults,
    TocDocument,
)
from .operational import OperationalContract, operational_contract, operational_contracts
from .periodical import Periodical
from .reference import ReferenceSpec, programmable_reference

__all__ = [
    "CATEGORY_CQL_FIELDS",
    "Categories",
    "CategoryValue",
    "CapabilityEvidence",
    "CapabilitySpec",
    "ContentSearchItem",
    "ContentSearchMatch",
    "ContentSearchResults",
    "Corpus",
    "CorpusArtifactFailure",
    "CorpusArtifactRecord",
    "CorpusItemResult",
    "CorpusReport",
    "Document",
    "DocumentMetadata",
    "DublinCoreRecord",
    "EvidenceAttestation",
    "EvidenceAttestationRecord",
    "EvidenceFreshness",
    "EvidenceSpec",
    "Gallica",
    "GallicaError",
    "GallicaResponseError",
    "OperationalContract",
    "Page",
    "Pagination",
    "PaginationPage",
    "Periodical",
    "ReferenceSpec",
    "SearchResults",
    "TocDocument",
    "__version__",
    "build_evidence_attestation",
    "capabilities",
    "capability_evidence",
    "evidence",
    "evidence_freshness",
    "load_evidence_attestation",
    "operational_contract",
    "operational_contracts",
    "programmable_reference",
]

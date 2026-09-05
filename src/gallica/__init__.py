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
    ContentSearchItem,
    ContentSearchResults,
    DocumentMetadata,
    DublinCoreRecord,
    SearchResults,
)
from .operational import OperationalContract, operational_contract, operational_contracts
from .periodical import Periodical
from .reference import ReferenceSpec, programmable_reference

__all__ = [
    "CapabilityEvidence",
    "CapabilitySpec",
    "ContentSearchItem",
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
    "Periodical",
    "ReferenceSpec",
    "SearchResults",
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

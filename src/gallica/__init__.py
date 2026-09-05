from ._version import __version__
from .agent import CapabilitySpec, capabilities
from .client import Gallica
from .corpus import Corpus, CorpusArtifactRecord, CorpusItemResult, CorpusReport
from .document import Document, Page
from .evidence import (
    CapabilityEvidence,
    EvidenceFreshness,
    EvidenceSpec,
    capability_evidence,
    evidence,
    evidence_freshness,
)
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
    "CorpusArtifactRecord",
    "CorpusItemResult",
    "CorpusReport",
    "Document",
    "DocumentMetadata",
    "DublinCoreRecord",
    "EvidenceFreshness",
    "EvidenceSpec",
    "Gallica",
    "OperationalContract",
    "Page",
    "Periodical",
    "ReferenceSpec",
    "SearchResults",
    "__version__",
    "capabilities",
    "capability_evidence",
    "evidence",
    "evidence_freshness",
    "operational_contract",
    "operational_contracts",
    "programmable_reference",
]

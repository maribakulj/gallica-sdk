from .agent import CapabilitySpec, capabilities
from .client import Gallica
from .corpus import Corpus, CorpusItemResult, CorpusReport
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
from .periodical import Periodical
from .reference import ReferenceSpec, programmable_reference

__all__ = [
    "CapabilityEvidence",
    "CapabilitySpec",
    "ContentSearchItem",
    "ContentSearchResults",
    "Corpus",
    "CorpusItemResult",
    "CorpusReport",
    "Document",
    "DocumentMetadata",
    "DublinCoreRecord",
    "EvidenceFreshness",
    "EvidenceSpec",
    "Gallica",
    "Page",
    "Periodical",
    "ReferenceSpec",
    "SearchResults",
    "capabilities",
    "capability_evidence",
    "evidence",
    "evidence_freshness",
    "programmable_reference",
]

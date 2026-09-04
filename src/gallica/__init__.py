from .agent import CapabilitySpec, capabilities
from .client import Gallica
from .corpus import Corpus, CorpusItemResult, CorpusReport
from .document import Document, Page
from .evidence import (
    CapabilityEvidence,
    EvidenceSpec,
    capability_evidence,
    evidence,
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
    "EvidenceSpec",
    "Gallica",
    "Page",
    "Periodical",
    "ReferenceSpec",
    "SearchResults",
    "capabilities",
    "capability_evidence",
    "evidence",
    "programmable_reference",
]

from .agent import CapabilitySpec, capabilities
from .client import Gallica
from .corpus import Corpus, CorpusItemResult, CorpusReport
from .document import Document, Page
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
    "CapabilitySpec",
    "ContentSearchItem",
    "ContentSearchResults",
    "Corpus",
    "CorpusItemResult",
    "CorpusReport",
    "Document",
    "DocumentMetadata",
    "DublinCoreRecord",
    "Gallica",
    "Page",
    "Periodical",
    "ReferenceSpec",
    "SearchResults",
    "capabilities",
    "programmable_reference",
]

from .client import Gallica
from .document import Document, Page
from .models import (
    ContentSearchItem,
    ContentSearchResults,
    DocumentMetadata,
    DublinCoreRecord,
    SearchResults,
)
from .periodical import Periodical

__all__ = [
    "ContentSearchItem",
    "ContentSearchResults",
    "Document",
    "DocumentMetadata",
    "DublinCoreRecord",
    "Gallica",
    "Page",
    "Periodical",
    "SearchResults",
]

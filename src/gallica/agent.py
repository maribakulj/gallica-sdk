from __future__ import annotations

from typing import TypedDict


class ParameterSpec(TypedDict, total=False):
    name: str
    type: str
    required: bool
    default: object
    description: str


class CapabilitySpec(TypedDict):
    id: str
    call: str
    description: str
    returns: str
    network_service: str
    parameters: tuple[ParameterSpec, ...]
    constraints: tuple[str, ...]


CAPABILITIES: tuple[CapabilitySpec, ...] = (
    {"id": "document", "call": "Gallica.document", "description": "Create a normalized document handle for a Gallica ARK.", "returns": "Document", "network_service": "none; local handle construction", "parameters": ({"name": "ark", "type": "str", "required": True},), "constraints": ("accepts bare identifiers, ark:/12148/... and canonical Gallica URLs",)},
    {"id": "periodical", "call": "Gallica.periodical", "description": "Create a periodical handle used to resolve dated issues.", "returns": "Periodical", "network_service": "none; local handle construction", "parameters": ({"name": "ark", "type": "str", "required": True},), "constraints": ("the ARK is normalized before use",)},
    {"id": "corpus", "call": "Gallica.corpus", "description": "Create an ordered, deduplicated corpus from Gallica ARKs.", "returns": "Corpus", "network_service": "none; local corpus construction", "parameters": ({"name": "arks", "type": "Iterable[str]", "required": True},), "constraints": ("ARKs are normalized and deduplicated while preserving first-seen order",)},
    {"id": "search", "call": "Gallica.search", "description": "Search Gallica through SRU 1.2 and return one typed result page.", "returns": "SearchResults", "network_service": "SRU 1.2", "parameters": ({"name": "query", "type": "str", "required": True, "description": "SRU/CQL query."}, {"name": "start_record", "type": "int", "required": False, "default": 1}, {"name": "maximum_records", "type": "int", "required": False, "default": 50}), "constraints": ("maximum_records must be between 1 and 50",)},
    {"id": "categories", "call": "Gallica.categories", "description": "Retrieve typed Gallica search-refinement categories for an SRU/CQL query.", "returns": "Categories", "network_service": "services/Categories", "parameters": ({"name": "query", "type": "str", "required": True, "description": "SRU/CQL query to aggregate."},), "constraints": ("empty queries are rejected", "the service returns at most 20 values per category", "howMany counts are approximate", "some categories are not exhaustive", "raw JSON remains available as raw_json")},
    {"id": "search_all", "call": "Gallica.search_all", "description": "Iterate lazily over paginated SRU results without manually managing startRecord.", "returns": "Iterator[DublinCoreRecord]", "network_service": "SRU 1.2", "parameters": ({"name": "query", "type": "str", "required": True, "description": "SRU/CQL query."}, {"name": "limit", "type": "int | None", "required": False, "default": None}, {"name": "page_size", "type": "int", "required": False, "default": 50}), "constraints": ("page_size must be between 1 and 50", "limit must be >= 1 when supplied", "results are fetched lazily page by page")},
    {"id": "document_metadata", "call": "Document.metadata", "description": "Retrieve OAIRecord metadata as typed Dublin Core plus Gallica technical fields.", "returns": "DocumentMetadata", "network_service": "services/OAIRecord", "parameters": (), "constraints": ("raw XML remains available as raw_xml",)},
    {"id": "document_pagination", "call": "Document.pagination", "description": "Retrieve the full typed Pagination structure, including logical page labels and document navigation metadata.", "returns": "Pagination", "network_service": "services/Pagination", "parameters": (), "constraints": ("view orders are 1-based", "raw XML remains available as raw_xml")},
    {"id": "document_page_count", "call": "Document.page_count", "description": "Return the number of image views reported by Gallica Pagination.", "returns": "int", "network_service": "services/Pagination", "parameters": (), "constraints": ("projects Pagination.image_views",)},
    {"id": "document_toc", "call": "Document.toc", "description": "Retrieve a Gallica table of contents while preserving whether the upstream representation is legacy HTML or TEI XML.", "returns": "TocDocument", "network_service": "services/Toc", "parameters": (), "constraints": ("returns format='html' for legacy TOCs and format='tei' for TEI XML", "raw upstream content is preserved")},
    {"id": "document_text", "call": "Document.text", "description": "Retrieve plain OCR text for a document.", "returns": "str", "network_service": ".texteBrut", "parameters": (), "constraints": ("public quota documented as 5 requests/minute",)},
    {"id": "content_search", "call": "Document.search_text", "description": "Search within OCR and return one typed ContentSearch page plus raw XML.", "returns": "ContentSearchResults", "network_service": "services/ContentSearch", "parameters": ({"name": "query", "type": "str", "required": True}, {"name": "page", "type": "int | None", "required": False, "default": None}, {"name": "start_result", "type": "int | None", "required": False, "default": None}), "constraints": ("page and start_result must be >= 1 when supplied", "the public service returns at most 10 items per request", "when page is supplied, OCR word rectangles are returned relative to p_width/p_height", "raw XML remains available as raw_xml")},
    {"id": "content_search_all", "call": "Document.search_text_all", "description": "Iterate lazily over ContentSearch results without manually managing startResult.", "returns": "Iterator[ContentSearchItem]", "network_service": "services/ContentSearch", "parameters": ({"name": "query", "type": "str", "required": True}, {"name": "page", "type": "int | None", "required": False, "default": None}, {"name": "limit", "type": "int | None", "required": False, "default": None}), "constraints": ("page must be >= 1 when supplied", "limit must be >= 1 when supplied", "pagination is lazy and follows the service's 10-item page cap")},
    {"id": "page_text", "call": "Page.text", "description": "Retrieve plain OCR text for exactly one Gallica view.", "returns": "str", "network_service": ".texteBrut", "parameters": (), "constraints": ("public quota documented as 5 requests/minute",)},
    {"id": "page_alto", "call": "Page.alto", "description": "Retrieve raw ALTO XML bytes for one view.", "returns": "bytes", "network_service": "RequestDigitalElement E=ALTO", "parameters": (), "constraints": ("view numbers are 1-based",)},
    {"id": "page_iiif_info", "call": "Page.iiif_info", "description": "Retrieve IIIF Image API info.json for one view.", "returns": "dict[str, object]", "network_service": "IIIF Image info.json", "parameters": (), "constraints": ("Image API is distinct from IIIF Presentation",)},
    {"id": "page_image", "call": "Page.image", "description": "Retrieve one IIIF image with a conservative default width.", "returns": "bytes", "network_service": "IIIF Image", "parameters": ({"name": "width", "type": "int", "required": False, "default": 1000}, {"name": "fmt", "type": "str", "required": False, "default": "jpg"}), "constraints": ("width must be >= 1", "width > 1000 uses the HD rate bucket", "1000px is the recommended default")},
    {"id": "periodical_issue", "call": "Periodical.issue", "description": "Resolve a periodical issue for an exact calendar date.", "returns": "Document | None", "network_service": "services/Issues", "parameters": ({"name": "when", "type": "datetime.date", "required": True},), "constraints": ("resolution uses dayOfYear from the Issues response",)},
    {"id": "corpus_fetch", "call": "Corpus.fetch", "description": "Fetch resumable corpus artifacts with atomic writes and per-artifact failure isolation.", "returns": "CorpusReport", "network_service": "composition of supported SDK primitives", "parameters": ({"name": "output", "type": "str | Path", "required": True}, {"name": "metadata", "type": "bool", "required": False, "default": True}, {"name": "text", "type": "bool", "required": False, "default": False}, {"name": "alto", "type": "bool", "required": False, "default": False}, {"name": "images", "type": "bool", "required": False, "default": False}, {"name": "views", "type": "Iterable[int] | None", "required": False, "default": None}, {"name": "image_width", "type": "int", "required": False, "default": 1000}, {"name": "resume", "type": "bool", "required": False, "default": True}), "constraints": ("ALTO or images require explicit views", "there is no implicit all-pages mode", "resume validates request fingerprint, byte size and SHA-256", "ordinary per-artifact failures do not stop independent artifacts or later ARKs")},
)


def capabilities() -> tuple[CapabilitySpec, ...]:
    """Return the stable machine-readable capability description."""
    return CAPABILITIES

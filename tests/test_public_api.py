from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import fields

import gallica
from gallica import (
    Categories,
    CategoryValue,
    ContentSearchItem,
    ContentSearchMatch,
    ContentSearchResults,
    Corpus,
    CorpusArtifactFailure,
    CorpusArtifactRecord,
    CorpusItemResult,
    CorpusReport,
    Document,
    DocumentMetadata,
    DublinCoreRecord,
    Gallica,
    IIIFImageInfo,
    IIIFPresentationManifest,
    Page,
    Pagination,
    PaginationPage,
    Periodical,
    SearchResults,
    TocDocument,
)

EXPECTED_ROOT_EXPORTS = (
    "CATEGORY_CQL_FIELDS",
    "CapabilityEvidence",
    "CapabilitySpec",
    "Categories",
    "CategoryValue",
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
    "IIIFImageInfo",
    "IIIFPresentationManifest",
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
)

EXPECTED_MODEL_FIELDS: tuple[tuple[type[object], tuple[str, ...]], ...] = (
    (DublinCoreRecord, ("fields",)),
    (SearchResults, ("query", "total", "records", "raw_xml")),
    (CategoryValue, ("category", "clean_value", "approximate_count", "label")),
    (Categories, ("query", "values", "raw_json")),
    (DocumentMetadata, ("ark", "record", "indexing_mode", "ocr_quality", "raw_xml")),
    (PaginationPage, ("number", "order", "pagination_type", "legend")),
    (
        Pagination,
        (
            "first_displayed_page",
            "has_toc",
            "toc_location",
            "has_content",
            "digital_id",
            "image_views",
            "audio_views",
            "pages",
            "raw_xml",
        ),
    ),
    (TocDocument, ("format", "raw", "well_formed")),
    (
        IIIFPresentationManifest,
        ("version", "identifier", "context", "canvas_count", "raw_json"),
    ),
    (
        IIIFImageInfo,
        ("version", "identifier", "context", "protocol", "profiles", "width", "height", "raw_json"),
    ),
    (ContentSearchMatch, ("alto_id", "hpos", "vpos", "width", "height")),
    (
        ContentSearchItem,
        ("page_id", "content_html", "alto_id", "score", "page_width", "page_height", "matches"),
    ),
    (ContentSearchResults, ("query", "total", "items", "raw_xml")),
    (
        CorpusArtifactRecord,
        ("kind", "path", "fingerprint", "sha256", "size", "parameters", "sdk_version"),
    ),
    (
        CorpusArtifactFailure,
        ("kind", "path", "fingerprint", "parameters", "error_type", "message", "retryable", "sdk_version"),
    ),
    (
        CorpusItemResult,
        (
            "ark",
            "status",
            "metadata_path",
            "text_path",
            "alto_paths",
            "image_paths",
            "artifacts",
            "failure_details",
            "error",
        ),
    ),
    (CorpusReport, ("items", "manifest_path")),
)


def _parameter_shape(callable_: Callable[..., object]) -> tuple[tuple[str, str, object], ...]:
    shape: list[tuple[str, str, object]] = []
    for parameter in inspect.signature(callable_).parameters.values():
        if parameter.name in {"self", "cls"}:
            continue
        default: object
        if parameter.default is inspect.Parameter.empty:
            default = "<required>"
        else:
            default = parameter.default
        shape.append((parameter.name, parameter.kind.name, default))
    return tuple(shape)


def test_root_exports_are_the_audited_release_surface() -> None:
    assert tuple(gallica.__all__) == EXPECTED_ROOT_EXPORTS
    for name in EXPECTED_ROOT_EXPORTS:
        assert hasattr(gallica, name), name


def test_typed_result_fields_are_the_audited_release_schema() -> None:
    for model, expected in EXPECTED_MODEL_FIELDS:
        assert tuple(field.name for field in fields(model)) == expected, model.__name__


def test_core_constructor_and_factory_shapes_are_stable() -> None:
    assert _parameter_shape(Gallica) == (("transport", "POSITIONAL_OR_KEYWORD", None),)
    assert _parameter_shape(Gallica.close) == ()
    assert _parameter_shape(Gallica.capabilities) == ()
    assert _parameter_shape(Gallica.document) == (("ark", "POSITIONAL_OR_KEYWORD", "<required>"),)
    assert _parameter_shape(Gallica.periodical) == (("ark", "POSITIONAL_OR_KEYWORD", "<required>"),)
    assert _parameter_shape(Gallica.corpus) == (("arks", "POSITIONAL_OR_KEYWORD", "<required>"),)


def test_search_shapes_are_stable() -> None:
    assert _parameter_shape(Gallica.search) == (
        ("query", "POSITIONAL_OR_KEYWORD", "<required>"),
        ("start_record", "KEYWORD_ONLY", 1),
        ("maximum_records", "KEYWORD_ONLY", 50),
    )
    assert _parameter_shape(Gallica.categories) == (
        ("query", "POSITIONAL_OR_KEYWORD", "<required>"),
    )
    assert _parameter_shape(Gallica.search_all) == (
        ("query", "POSITIONAL_OR_KEYWORD", "<required>"),
        ("limit", "KEYWORD_ONLY", None),
        ("page_size", "KEYWORD_ONLY", 50),
    )


def test_document_and_page_shapes_are_stable() -> None:
    for method in (
        Document.metadata,
        Document.pagination,
        Document.page_count,
        Document.toc,
        Document.iiif_manifest,
        Document.text,
        Page.text,
        Page.alto,
        Page.iiif_info,
    ):
        assert _parameter_shape(method) == ()

    assert _parameter_shape(Document.search_text) == (
        ("query", "POSITIONAL_OR_KEYWORD", "<required>"),
        ("page", "KEYWORD_ONLY", None),
        ("start_result", "KEYWORD_ONLY", None),
    )
    assert _parameter_shape(Document.search_text_all) == (
        ("query", "POSITIONAL_OR_KEYWORD", "<required>"),
        ("page", "KEYWORD_ONLY", None),
        ("limit", "KEYWORD_ONLY", None),
    )
    assert _parameter_shape(Document.page) == (
        ("number", "POSITIONAL_OR_KEYWORD", "<required>"),
    )
    assert _parameter_shape(Page.image) == (
        ("width", "KEYWORD_ONLY", 1000),
        ("fmt", "KEYWORD_ONLY", "jpg"),
    )


def test_result_helper_shapes_are_stable() -> None:
    assert _parameter_shape(DublinCoreRecord.values) == (
        ("name", "POSITIONAL_OR_KEYWORD", "<required>"),
    )
    assert _parameter_shape(DublinCoreRecord.first) == (
        ("name", "POSITIONAL_OR_KEYWORD", "<required>"),
    )
    assert _parameter_shape(DublinCoreRecord.as_dict) == ()
    assert _parameter_shape(SearchResults.write_jsonl) == (
        ("path", "POSITIONAL_OR_KEYWORD", "<required>"),
    )
    assert _parameter_shape(Categories.for_category) == (
        ("category", "POSITIONAL_OR_KEYWORD", "<required>"),
    )


def test_periodical_and_corpus_shapes_are_stable() -> None:
    assert _parameter_shape(Periodical.issue) == (
        ("when", "POSITIONAL_OR_KEYWORD", "<required>"),
    )
    assert _parameter_shape(Corpus.fetch) == (
        ("output", "POSITIONAL_OR_KEYWORD", "<required>"),
        ("metadata", "KEYWORD_ONLY", True),
        ("text", "KEYWORD_ONLY", False),
        ("alto", "KEYWORD_ONLY", False),
        ("images", "KEYWORD_ONLY", False),
        ("views", "KEYWORD_ONLY", None),
        ("image_width", "KEYWORD_ONLY", 1000),
        ("resume", "KEYWORD_ONLY", True),
    )

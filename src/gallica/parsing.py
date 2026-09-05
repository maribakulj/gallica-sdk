from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict

from .exceptions import GallicaResponseError
from .models import (
    ContentSearchItem,
    ContentSearchMatch,
    ContentSearchResults,
    DocumentMetadata,
    DublinCoreRecord,
    SearchResults,
)

_DC_NS = "http://purl.org/dc/elements/1.1/"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_xml(xml: str, *, expected_root: str) -> ET.Element:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise GallicaResponseError(f"invalid XML response for {expected_root}") from exc
    if _local_name(root.tag) != expected_root:
        raise GallicaResponseError(
            f"unexpected XML root {_local_name(root.tag)!r}; expected {expected_root!r}"
        )
    return root


def _dc_record(element: ET.Element) -> DublinCoreRecord:
    values: dict[str, list[str]] = defaultdict(list)
    for child in element:
        if child.tag.startswith(f"{{{_DC_NS}}}") and child.text:
            text = child.text.strip()
            if text:
                values[_local_name(child.tag)].append(text)
    return DublinCoreRecord({name: tuple(items) for name, items in values.items()})


def parse_sru(xml: str, *, fallback_query: str) -> SearchResults:
    root = _parse_xml(xml, expected_root="searchRetrieveResponse")
    total = 0
    query = fallback_query
    records: list[DublinCoreRecord] = []

    for element in root.iter():
        name = _local_name(element.tag)
        if name == "numberOfRecords" and element.text:
            try:
                total = int(element.text)
            except ValueError as exc:
                raise GallicaResponseError("SRU numberOfRecords is not an integer") from exc
        elif name == "query" and element.text and query == fallback_query:
            query = element.text.strip()
        elif name == "dc" and element.tag.endswith("}dc"):
            records.append(_dc_record(element))

    return SearchResults(query=query, total=total, records=tuple(records), raw_xml=xml)


def parse_oai_record(xml: str, *, ark: str) -> DocumentMetadata:
    root = _parse_xml(xml, expected_root="results")
    dc_element: ET.Element | None = None
    indexing_mode: str | None = None
    ocr_quality: float | None = None

    for element in root.iter():
        name = _local_name(element.tag)
        if name == "dc" and element.tag.endswith("}dc") and dc_element is None:
            dc_element = element
        elif name == "mode_indexation" and element.text:
            indexing_mode = element.text.strip() or None
        elif name == "nqamoyen" and element.text:
            try:
                ocr_quality = float(element.text.strip())
            except ValueError:
                ocr_quality = None

    record = _dc_record(dc_element) if dc_element is not None else DublinCoreRecord({})
    return DocumentMetadata(
        ark=ark,
        record=record,
        indexing_mode=indexing_mode,
        ocr_quality=ocr_quality,
        raw_xml=xml,
    )


def _optional_int_text(element: ET.Element | None, *, field: str) -> int | None:
    if element is None or element.text is None or not element.text.strip():
        return None
    try:
        return int(element.text.strip())
    except ValueError as exc:
        raise GallicaResponseError(f"ContentSearch {field} is not an integer") from exc


def _required_int_attr(element: ET.Element, name: str) -> int:
    raw = element.attrib.get(name)
    if raw is None:
        raise GallicaResponseError(f"ContentSearch altoidstring lacks {name}")
    try:
        return int(raw)
    except ValueError as exc:
        raise GallicaResponseError(
            f"ContentSearch altoidstring {name} is not an integer"
        ) from exc


def _content_search_matches(item: ET.Element) -> tuple[ContentSearchMatch, ...]:
    matches: list[ContentSearchMatch] = []
    for element in item.iter():
        if _local_name(element.tag) != "altoidstring":
            continue
        alto_id = (element.text or "").strip()
        if not alto_id:
            raise GallicaResponseError("ContentSearch altoidstring lacks an OCR identifier")
        matches.append(
            ContentSearchMatch(
                alto_id=alto_id,
                hpos=_required_int_attr(element, "hpos"),
                vpos=_required_int_attr(element, "vpos"),
                width=_required_int_attr(element, "width"),
                height=_required_int_attr(element, "height"),
            )
        )
    return tuple(matches)


def parse_content_search(xml: str, *, fallback_query: str) -> ContentSearchResults:
    root = _parse_xml(xml, expected_root="results")
    total_raw = root.attrib.get("countResults", "0")
    try:
        total = int(total_raw)
    except ValueError as exc:
        raise GallicaResponseError("ContentSearch countResults is not an integer") from exc

    query = fallback_query
    items: list[ContentSearchItem] = []
    for child in root:
        if _local_name(child.tag) == "query" and child.text:
            query = child.text.strip()

    for element in root.iter():
        if _local_name(element.tag) != "item":
            continue
        direct_children = {_local_name(child.tag): child for child in element}
        matches = _content_search_matches(element)
        score: float | None = None
        raw_score = element.attrib.get("score")
        if raw_score:
            try:
                score = float(raw_score)
            except ValueError as exc:
                raise GallicaResponseError("ContentSearch score is not numeric") from exc
        page_id_element = direct_children.get("p_id")
        content_element = direct_children.get("content")
        items.append(
            ContentSearchItem(
                page_id=(page_id_element.text.strip() if page_id_element is not None and page_id_element.text else None),
                content_html=(content_element.text if content_element is not None and content_element.text else None),
                alto_id=matches[0].alto_id if matches else None,
                score=score,
                page_width=_optional_int_text(direct_children.get("p_width"), field="p_width"),
                page_height=_optional_int_text(direct_children.get("p_height"), field="p_height"),
                matches=matches,
            )
        )

    return ContentSearchResults(query=query, total=total, items=tuple(items), raw_xml=xml)

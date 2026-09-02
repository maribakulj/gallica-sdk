from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict

from .models import (
    ContentSearchItem,
    ContentSearchResults,
    DocumentMetadata,
    DublinCoreRecord,
    SearchResults,
)

_DC_NS = "http://purl.org/dc/elements/1.1/"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _dc_record(element: ET.Element) -> DublinCoreRecord:
    values: dict[str, list[str]] = defaultdict(list)
    for child in element:
        if child.tag.startswith(f"{{{_DC_NS}}}") and child.text:
            text = child.text.strip()
            if text:
                values[_local_name(child.tag)].append(text)
    return DublinCoreRecord({name: tuple(items) for name, items in values.items()})


def parse_sru(xml: str, *, fallback_query: str) -> SearchResults:
    root = ET.fromstring(xml)
    total = 0
    query = fallback_query
    records: list[DublinCoreRecord] = []

    for element in root.iter():
        name = _local_name(element.tag)
        if name == "numberOfRecords" and element.text:
            total = int(element.text)
        elif name == "query" and element.text and query == fallback_query:
            query = element.text.strip()
        elif name == "dc" and element.tag.endswith("}dc"):
            records.append(_dc_record(element))

    return SearchResults(query=query, total=total, records=tuple(records), raw_xml=xml)


def parse_oai_record(xml: str, *, ark: str) -> DocumentMetadata:
    root = ET.fromstring(xml)
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


def parse_content_search(xml: str, *, fallback_query: str) -> ContentSearchResults:
    root = ET.fromstring(xml)
    total_raw = root.attrib.get("countResults", "0")
    try:
        total = int(total_raw)
    except ValueError:
        total = 0

    query = fallback_query
    items: list[ContentSearchItem] = []
    for child in root:
        if _local_name(child.tag) == "query" and child.text:
            query = child.text.strip()

    for element in root.iter():
        if _local_name(element.tag) != "item":
            continue
        children = {_local_name(child.tag): child.text for child in element}
        score: float | None = None
        raw_score = element.attrib.get("score")
        if raw_score:
            try:
                score = float(raw_score)
            except ValueError:
                pass
        items.append(
            ContentSearchItem(
                page_id=(children.get("p_id") or None),
                content_html=(children.get("content") or None),
                alto_id=(children.get("altoid") or None),
                score=score,
            )
        )

    return ContentSearchResults(query=query, total=total, items=tuple(items), raw_xml=xml)

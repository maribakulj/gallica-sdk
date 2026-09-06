from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class DublinCoreRecord:
    """A Dublin Core record preserving repeated values."""

    fields: Mapping[str, tuple[str, ...]]

    def values(self, name: str) -> tuple[str, ...]:
        return self.fields.get(name, ())

    def first(self, name: str) -> str | None:
        values = self.values(name)
        return values[0] if values else None

    @property
    def title(self) -> str | None:
        return self.first("title")

    @property
    def identifiers(self) -> tuple[str, ...]:
        return self.values("identifier")

    @property
    def ark(self) -> str | None:
        marker = "/ark:/12148/"
        for identifier in self.identifiers:
            if marker in identifier:
                tail = identifier.split(marker, 1)[1]
                return tail.split("/", 1)[0]
        return None

    def as_dict(self) -> dict[str, object]:
        return {
            "ark": self.ark,
            "fields": {name: list(values) for name, values in self.fields.items()},
        }


@dataclass(frozen=True, slots=True)
class SearchResults:
    query: str
    total: int
    records: tuple[DublinCoreRecord, ...]
    raw_xml: str

    def __iter__(self) -> Iterator[DublinCoreRecord]:
        return iter(self.records)

    def __len__(self) -> int:
        return len(self.records)

    @property
    def arks(self) -> tuple[str, ...]:
        return tuple(record.ark for record in self.records if record.ark is not None)

    def write_jsonl(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as stream:
            for record in self.records:
                stream.write(json.dumps(record.as_dict(), ensure_ascii=False, sort_keys=True))
                stream.write("\n")
        return output


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    ark: str
    record: DublinCoreRecord
    indexing_mode: str | None
    ocr_quality: float | None
    raw_xml: str


@dataclass(frozen=True, slots=True)
class PaginationPage:
    """One physical Gallica view as described by the Pagination service."""

    number: str | None
    order: int
    pagination_type: str | None
    legend: str | None = None


@dataclass(frozen=True, slots=True)
class Pagination:
    """Typed Gallica Pagination response with the original XML preserved."""

    first_displayed_page: int | None
    has_toc: bool | None
    toc_location: int | None
    has_content: bool | None
    digital_id: str | None
    image_views: int
    audio_views: int | None
    pages: tuple[PaginationPage, ...]
    raw_xml: str


@dataclass(frozen=True, slots=True)
class TocDocument:
    """Gallica TOC payload preserving the upstream HTML or TEI representation."""

    format: Literal["html", "tei"]
    raw: str
    well_formed: bool | None


@dataclass(frozen=True, slots=True)
class ContentSearchMatch:
    """One OCR word rectangle returned by ContentSearch with ``page``."""

    alto_id: str
    hpos: int
    vpos: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ContentSearchItem:
    page_id: str | None
    content_html: str | None
    alto_id: str | None
    score: float | None
    page_width: int | None = None
    page_height: int | None = None
    matches: tuple[ContentSearchMatch, ...] = ()


@dataclass(frozen=True, slots=True)
class ContentSearchResults:
    query: str
    total: int
    items: tuple[ContentSearchItem, ...]
    raw_xml: str

    def __iter__(self) -> Iterator[ContentSearchItem]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass


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


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    ark: str
    record: DublinCoreRecord
    indexing_mode: str | None
    ocr_quality: float | None
    raw_xml: str


@dataclass(frozen=True, slots=True)
class ContentSearchItem:
    page_id: str | None
    content_html: str | None
    alto_id: str | None
    score: float | None


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

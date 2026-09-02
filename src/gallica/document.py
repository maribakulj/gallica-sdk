from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .models import ContentSearchResults, DocumentMetadata

if TYPE_CHECKING:
    from .client import Gallica


@dataclass(frozen=True, slots=True)
class Document:
    _gallica: Gallica
    ark: str

    def metadata(self) -> DocumentMetadata:
        """Return typed Dublin Core and technical OAIRecord metadata."""
        return self._gallica._metadata(self.ark)

    def page_count(self) -> int:
        """Return the number of image views reported by Pagination."""
        return self._gallica._page_count(self.ark)

    def text(self) -> str:
        """Return the document OCR text through Gallica's .texteBrut representation."""
        return self._gallica._text(self.ark)

    def search_text(
        self,
        query: str,
        *,
        page: int | None = None,
        start_result: int | None = None,
    ) -> ContentSearchResults:
        """Search within OCR and return typed ContentSearch results."""
        return self._gallica._content_search(
            self.ark,
            query,
            page=page,
            start_result=start_result,
        )

    def page(self, number: int) -> Page:
        if number < 1:
            raise ValueError("page number must be >= 1")
        return Page(self._gallica, self.ark, number)


@dataclass(frozen=True, slots=True)
class Page:
    _gallica: Gallica
    ark: str
    number: int

    def text(self) -> str:
        """Return OCR text for this single Gallica view."""
        return self._gallica._text(self.ark, start_view=self.number, nviews=1)

    def alto(self) -> bytes:
        """Return the raw ALTO XML bytes for this view."""
        return self._gallica._alto(self.ark, self.number)

    def iiif_info(self) -> dict[str, object]:
        """Return the IIIF Image API info.json object for this view."""
        return self._gallica._iiif_info(self.ark, self.number)

    def image(self, *, width: int = 1000, fmt: str = "jpg") -> bytes:
        """Return an IIIF image; 1000 px is the conservative default width."""
        return self._gallica._image(self.ark, self.number, width=width, fmt=fmt)

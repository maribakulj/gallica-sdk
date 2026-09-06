from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .models import (
    ContentSearchItem,
    ContentSearchResults,
    DocumentMetadata,
    Pagination,
    TocDocument,
)

if TYPE_CHECKING:
    from .client import Gallica


@dataclass(frozen=True, slots=True)
class Document:
    _gallica: Gallica
    ark: str

    def metadata(self) -> DocumentMetadata:
        """Return typed Dublin Core and technical OAIRecord metadata."""
        return self._gallica._metadata(self.ark)

    def pagination(self) -> Pagination:
        """Return the complete typed Pagination structure for this document."""
        return self._gallica._pagination(self.ark)

    def page_count(self) -> int:
        """Return the number of image views reported by Pagination."""
        return self.pagination().image_views

    def toc(self) -> TocDocument:
        """Return the table of contents as legacy HTML or TEI XML."""
        return self._gallica._toc(self.ark)

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
        """Search within OCR and return one ContentSearch result page.

        Passing ``page`` asks Gallica for OCR word rectangles relative to the master
        image dimensions for that one physical view.
        """
        return self._gallica._content_search(
            self.ark,
            query,
            page=page,
            start_result=start_result,
        )

    def search_text_all(
        self,
        query: str,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> Iterator[ContentSearchItem]:
        """Iterate lazily over ContentSearch results using ``startResult`` pagination."""
        if page is not None and page < 1:
            raise ValueError("page must be >= 1")
        if limit is not None and limit < 1:
            raise ValueError("limit must be >= 1 when supplied")

        yielded = 0
        start_result = 1
        while True:
            result_page = self.search_text(
                query,
                page=page,
                start_result=start_result,
            )
            if not result_page.items:
                return
            for item in result_page.items:
                yield item
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            start_result += len(result_page.items)
            if start_result > result_page.total:
                return

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

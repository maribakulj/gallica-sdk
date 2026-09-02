from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Gallica


@dataclass(frozen=True, slots=True)
class Document:
    _gallica: "Gallica"
    ark: str

    def metadata(self) -> str:
        """Return the raw OAIRecord XML for this document."""
        return self._gallica._metadata(self.ark)

    def page_count(self) -> int:
        """Return the number of image views reported by Pagination."""
        return self._gallica._page_count(self.ark)

    def page(self, number: int) -> "Page":
        if number < 1:
            raise ValueError("page number must be >= 1")
        return Page(self._gallica, self.ark, number)


@dataclass(frozen=True, slots=True)
class Page:
    _gallica: "Gallica"
    ark: str
    number: int

    def alto(self) -> bytes:
        """Return the raw ALTO XML bytes for this view."""
        return self._gallica._alto(self.ark, self.number)

    def iiif_info(self) -> dict[str, object]:
        """Return the IIIF Image API info.json object for this view."""
        return self._gallica._iiif_info(self.ark, self.number)

    def image(self, *, width: int = 1000, fmt: str = "jpg") -> bytes:
        """Return an IIIF image; 1000 px is the conservative default width."""
        return self._gallica._image(self.ark, self.number, width=width, fmt=fmt)

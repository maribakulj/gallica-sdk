from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Gallica
    from .document import Document


@dataclass(frozen=True, slots=True)
class Periodical:
    _gallica: Gallica
    ark: str

    def issue(self, when: date) -> Document | None:
        """Resolve one dated issue and return it as a Document when available."""
        issue_ark = self._gallica._issue_for_date(self.ark, when)
        if issue_ark is None:
            return None
        return self._gallica.document(issue_ark)

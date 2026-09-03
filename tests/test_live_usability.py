from __future__ import annotations

import pytest

from gallica import Gallica

pytestmark = pytest.mark.live


def test_public_search_all_paginates_and_exposes_arks() -> None:
    with Gallica() as gallica:
        records = list(gallica.search_all('gallica all "Verdun"', limit=3, page_size=2))
        assert len(records) == 3
        assert all(record.ark is not None for record in records)

        first_page = gallica.search('gallica all "Verdun"', maximum_records=3)
        assert len(first_page.arks) == 3
        corpus = gallica.corpus(first_page.arks)
        assert len(corpus) == 3

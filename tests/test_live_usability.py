from __future__ import annotations

import pytest

from gallica import Gallica, GallicaResponseError

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


def test_public_categories_exposes_or_safely_rejects_search_refinements() -> None:
    with Gallica() as gallica:
        try:
            categories = gallica.categories('gallica all "Verdun"')
        except GallicaResponseError as exc:
            # Gallica currently returns HTML/403 for Categories from cold public
            # runners. Rejecting that page instead of parsing it as JSON is the
            # expected safe behavior until public machine access is reproducible.
            assert "Categories returned HTML" in str(exc)
            return

        assert len(categories) > 0
        assert "language" in categories.categories
        assert "typedoc" in categories.categories

        language = categories.for_category("language")
        assert language
        assert all(item.approximate_count >= 0 for item in language)
        assert all(item.cql_field == "dc.language" for item in language)

        typedoc = categories.for_category("typedoc")
        assert typedoc
        assert all(item.cql_field == "dc.type" for item in typedoc)
        assert all(item.clean_value for item in typedoc)

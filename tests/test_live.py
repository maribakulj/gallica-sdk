from __future__ import annotations

import pytest

from gallica import Gallica

pytestmark = pytest.mark.live


def test_public_gallica_vertical_slice() -> None:
    with Gallica() as gallica:
        xml = gallica.search('gallica all "Verdun"', maximum_records=1)
        assert "searchRetrieveResponse" in xml

        doc = gallica.document("bpt6k5738219s")
        assert doc.page_count() == 374
        assert "results" in doc.metadata()

        alto = gallica.document("bpt6k5619759j").page(3).alto()
        assert len(alto) > 1000

        info = gallica.document("btv1b53066668g").page(1).iiif_info()
        assert int(info["width"]) > 1000

        image = gallica.document("btv1b53066668g").page(1).image(width=1000)
        assert len(image) > 1000

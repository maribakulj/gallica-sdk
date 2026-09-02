from __future__ import annotations

from datetime import date

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


def test_public_gallica_phase1_document_access() -> None:
    with Gallica() as gallica:
        text_doc = gallica.document("bpt6k5460422k")
        assert len(text_doc.text()) > 100
        assert len(text_doc.page(1).text()) > 10

        search_xml = text_doc.search_text("hugo", start_result=1)
        assert "results" in search_xml.lower()

        issue = gallica.periodical("cb32798952c").issue(date(1937, 3, 25))
        assert issue is not None
        assert issue.ark == "bpt6k5509212w"

        pdf = gallica.document("bc6p06zq4dn").page(1).pdf()
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 1000

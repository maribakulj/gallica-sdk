from __future__ import annotations

import httpx
import pytest

from gallica import Gallica, GallicaResponseError


class StaticTransport:
    def __init__(self, responses: dict[str, httpx.Response]) -> None:
        self.responses = responses

    def close(self) -> None:
        pass

    def get(self, url: str, *, params=None, bucket: str = "default") -> httpx.Response:
        del params, bucket
        for suffix, response in self.responses.items():
            if url.endswith(suffix):
                return response
        raise AssertionError(url)


def _response(content: bytes, *, content_type: str = "application/xml") -> httpx.Response:
    return httpx.Response(
        200,
        content=content,
        headers={"Content-Type": content_type},
        request=httpx.Request("GET", "https://gallica.bnf.fr/test"),
    )


def test_pagination_exposes_structure_and_logical_pages() -> None:
    xml = b"""<livre><structure><firstDisplayedPage>12</firstDisplayedPage><hasToc>true</hasToc><TocLocation>328</TocLocation><hasContent>true</hasContent><idUPN>NUMM-5738219</idUPN><nbVueImages>2</nbVueImages></structure><pages><page><numero>NP</numero><ordre>1</ordre><pagination_type>N</pagination_type></page><page><numero>I</numero><ordre>2</ordre><pagination_type>R</pagination_type><legend>Frontispice</legend></page></pages></livre>"""
    gallica = Gallica(transport=StaticTransport({"/services/Pagination": _response(xml)}))  # type: ignore[arg-type]
    pagination = gallica.document("bpt6k1").pagination()

    assert pagination.image_views == 2
    assert pagination.first_displayed_page == 12
    assert pagination.has_toc is True
    assert pagination.toc_location == 328
    assert pagination.has_content is True
    assert pagination.digital_id == "NUMM-5738219"
    assert pagination.pages[1].number == "I"
    assert pagination.pages[1].order == 2
    assert pagination.pages[1].pagination_type == "R"
    assert pagination.pages[1].legend == "Frontispice"
    assert gallica.document("bpt6k1").page_count() == 2


def test_pagination_rejects_invalid_page_order() -> None:
    xml = b"<livre><structure><nbVueImages>1</nbVueImages></structure><pages><page><ordre>zero</ordre></page></pages></livre>"
    gallica = Gallica(transport=StaticTransport({"/services/Pagination": _response(xml)}))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="ordre"):
        gallica.document("bpt6k1").pagination()


def test_toc_accepts_legacy_html() -> None:
    response = _response(b"<!DOCTYPE html><html><body>table</body></html>", content_type="text/html")
    gallica = Gallica(transport=StaticTransport({"/services/Toc": response}))  # type: ignore[arg-type]
    toc = gallica.document("bpt6k1").toc()
    assert toc.format == "html"
    assert toc.well_formed is None
    assert "table" in toc.raw


def test_toc_accepts_well_formed_tei_xml() -> None:
    response = _response(b"<TEI.2><text><body><div0 type='TdM'/></body></text></TEI.2>")
    gallica = Gallica(transport=StaticTransport({"/services/Toc": response}))  # type: ignore[arg-type]
    toc = gallica.document("bpt6k1").toc()
    assert toc.format == "tei"
    assert toc.well_formed is True
    assert "TEI.2" in toc.raw


def test_toc_preserves_recognizable_but_malformed_tei() -> None:
    response = _response(b"<?xml version='1.0'?><TEI.2><text>unescaped & value</text></TEI.2>")
    gallica = Gallica(transport=StaticTransport({"/services/Toc": response}))  # type: ignore[arg-type]
    toc = gallica.document("bpt6k1").toc()
    assert toc.format == "tei"
    assert toc.well_formed is False
    assert "unescaped & value" in toc.raw


def test_toc_rejects_unrecognized_malformed_payload() -> None:
    response = _response(b"<results><broken")
    gallica = Gallica(transport=StaticTransport({"/services/Toc": response}))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="neither recognizable HTML nor TEI"):
        gallica.document("bpt6k1").toc()


def test_toc_rejects_unexpected_xml() -> None:
    response = _response(b"<results/>")
    gallica = Gallica(transport=StaticTransport({"/services/Toc": response}))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="unexpected XML root"):
        gallica.document("bpt6k1").toc()

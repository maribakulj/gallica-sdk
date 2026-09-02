from __future__ import annotations

import json

import httpx

from gallica import Gallica
from gallica.ark import ark_uri, normalize_ark


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str] | None, str]] = []

    def close(self) -> None:
        pass

    def get(self, url: str, *, params=None, bucket: str = "default") -> httpx.Response:
        normalized = dict(params) if params is not None else None
        self.calls.append((url, normalized, bucket))
        request = httpx.Request("GET", url, params=params)
        if url.endswith("/services/Pagination"):
            return httpx.Response(200, content=b"<results><structure><nbVueImages>374</nbVueImages></structure></results>", request=request)
        if url.endswith("/services/OAIRecord"):
            xml = b'''<results xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"><notice><record><metadata><oai_dc:dc><dc:title>Example title</dc:title><dc:identifier>https://gallica.bnf.fr/ark:/12148/bpt6k5738219s</dc:identifier></oai_dc:dc></metadata></record></notice><mode_indexation>OCR</mode_indexation><nqamoyen>92.57</nqamoyen></results>'''
            return httpx.Response(200, content=xml, request=request)
        if url.endswith("/RequestDigitalElement"):
            return httpx.Response(200, content=b"<alto/>", request=request)
        if url.endswith("/info.json"):
            return httpx.Response(200, content=json.dumps({"width": 10784}).encode(), request=request)
        if "/iiif/" in url:
            return httpx.Response(200, content=b"jpeg", request=request)
        if url.endswith("/SRU"):
            xml = b'''<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"><srw:numberOfRecords>12</srw:numberOfRecords><srw:records><srw:record><srw:recordData><oai_dc:dc><dc:title>Verdun</dc:title><dc:creator>Auteur</dc:creator><dc:identifier>https://gallica.bnf.fr/ark:/12148/bpt6k123</dc:identifier></oai_dc:dc></srw:recordData></srw:record></srw:records></srw:searchRetrieveResponse>'''
            return httpx.Response(200, content=xml, request=request)
        raise AssertionError(f"Unexpected URL: {url}")


def test_ark_normalization_accepts_common_forms() -> None:
    expected = "bpt6k5738219s"
    assert normalize_ark(expected) == expected
    assert normalize_ark(f"ark:/12148/{expected}") == expected
    assert normalize_ark(f"https://gallica.bnf.fr/ark:/12148/{expected}") == expected
    assert ark_uri(expected) == f"ark:/12148/{expected}"


def test_document_and_page_vertical_slice() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]
    doc = gallica.document("ark:/12148/bpt6k5738219s")

    metadata = doc.metadata()
    assert metadata.record.title == "Example title"
    assert metadata.record.ark == "bpt6k5738219s"
    assert metadata.indexing_mode == "OCR"
    assert metadata.ocr_quality == 92.57
    assert doc.page_count() == 374

    page = doc.page(3)
    assert page.alto() == b"<alto/>"
    assert page.iiif_info()["width"] == 10784
    assert page.image() == b"jpeg"

    image_call = next(call for call in transport.calls if "/iiif/" in call[0] and not call[0].endswith("info.json"))
    assert "/full/1000,/0/native.jpg" in image_call[0]
    assert image_call[2] == "default"


def test_search_returns_typed_repeated_dublin_core_records() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    results = gallica.search('gallica all "Verdun"', maximum_records=1)
    assert results.total == 12
    assert len(results) == 1
    assert results.records[0].title == "Verdun"
    assert results.records[0].first("creator") == "Auteur"
    assert results.records[0].ark == "bpt6k123"
    assert "searchRetrieveResponse" in results.raw_xml

    try:
        gallica.search("x", maximum_records=51)
    except ValueError as exc:
        assert "between 1 and 50" in str(exc)
    else:
        raise AssertionError("maximum_records=51 should be rejected")


def test_hd_image_uses_hd_rate_bucket() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]
    gallica.document("bpt6k5738219s").page(1).image(width=3000)
    assert transport.calls[-1][2] == "iiif_hd"

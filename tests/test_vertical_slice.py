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
            return httpx.Response(200, content=b"<results><title>Example</title></results>", request=request)
        if url.endswith("/RequestDigitalElement"):
            return httpx.Response(200, content=b"<alto/>", request=request)
        if url.endswith("/info.json"):
            return httpx.Response(200, content=json.dumps({"width": 10784}).encode(), request=request)
        if "/iiif/" in url:
            return httpx.Response(200, content=b"jpeg", request=request)
        if url.endswith("/SRU"):
            return httpx.Response(200, content=b"<searchRetrieveResponse/>", request=request)
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

    assert doc.ark == "bpt6k5738219s"
    assert "Example" in doc.metadata()
    assert doc.page_count() == 374

    page = doc.page(3)
    assert page.alto() == b"<alto/>"
    assert page.iiif_info()["width"] == 10784
    assert page.image() == b"jpeg"

    image_call = next(call for call in transport.calls if "/iiif/" in call[0] and not call[0].endswith("info.json"))
    assert "/full/1000,/0/native.jpg" in image_call[0]
    assert image_call[2] == "default"


def test_search_enforces_sru_record_limit() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    assert "searchRetrieveResponse" in gallica.search('gallica all "Verdun"', maximum_records=1)

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

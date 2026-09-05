from __future__ import annotations

import json

import httpx
import pytest

from gallica import Gallica, GallicaResponseError


class StaticTransport:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    def close(self) -> None:
        pass

    def get(self, url: str, *, params=None, bucket: str = "default") -> httpx.Response:
        return self.response


def _response(
    content: bytes,
    *,
    content_type: str | None = None,
) -> httpx.Response:
    headers = {"Content-Type": content_type} if content_type is not None else None
    return httpx.Response(
        200,
        content=content,
        headers=headers,
        request=httpx.Request("GET", "https://gallica.bnf.fr/test"),
    )


def test_alto_rejects_html_success_payload() -> None:
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(b"<html><body>error</body></html>", content_type="text/html")
        )
    )
    with pytest.raises(GallicaResponseError, match="ALTO returned HTML"):
        gallica.document("bpt6k1").page(1).alto()


def test_alto_rejects_wrong_xml_root() -> None:
    gallica = Gallica(transport=StaticTransport(_response(b"<results/>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="unexpected root"):
        gallica.document("bpt6k1").page(1).alto()


def test_image_rejects_html_success_payload() -> None:
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(b"<!doctype html><html></html>", content_type="text/html")
        )
    )
    with pytest.raises(GallicaResponseError, match="IIIF image returned HTML"):
        gallica.document("bpt6k1").page(1).image()


def test_image_accepts_jpeg_signature_without_content_type() -> None:
    payload = b"\xff\xd8\xffpayload"
    gallica = Gallica(transport=StaticTransport(_response(payload)))  # type: ignore[arg-type]
    assert gallica.document("bpt6k1").page(1).image() == payload


def test_text_rejects_html_success_payload() -> None:
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(b"<html>not OCR</html>", content_type="text/html; charset=utf-8")
        )
    )
    with pytest.raises(GallicaResponseError, match="plain OCR text returned HTML"):
        gallica.document("bpt6k1").text()


def test_sru_rejects_html_root_even_with_http_200() -> None:
    gallica = Gallica(transport=StaticTransport(_response(b"<html><body>error</body></html>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="unexpected XML root"):
        gallica.search("test", maximum_records=1)


def test_content_search_rejects_invalid_count_results() -> None:
    gallica = Gallica(
        transport=StaticTransport(_response(b'<results countResults="not-a-number"/>'))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="countResults"):
        gallica.document("bpt6k1").search_text("test")


def test_iiif_info_requires_dimensions() -> None:
    payload = json.dumps({"width": 1000}).encode()
    gallica = Gallica(
        transport=StaticTransport(_response(payload, content_type="application/json"))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="width/height"):
        gallica.document("bpt6k1").page(1).iiif_info()

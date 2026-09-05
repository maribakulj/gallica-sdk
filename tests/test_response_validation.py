from __future__ import annotations

import json
from datetime import date

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
    url: str = "https://gallica.bnf.fr/test",
) -> httpx.Response:
    headers = {"Content-Type": content_type} if content_type is not None else None
    return httpx.Response(
        200,
        content=content,
        headers=headers,
        request=httpx.Request("GET", url),
    )


def test_alto_rejects_html_success_payload() -> None:
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(b"<html><body>error</body></html>", content_type="text/html")
        )
    )
    with pytest.raises(GallicaResponseError, match="ALTO returned HTML"):
        gallica.document("bpt6k1").page(1).alto()


def test_alto_rejects_malformed_xml() -> None:
    gallica = Gallica(transport=StaticTransport(_response(b"<alto>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="not valid XML"):
        gallica.document("bpt6k1").page(1).alto()


def test_alto_rejects_wrong_xml_root() -> None:
    gallica = Gallica(transport=StaticTransport(_response(b"<results/>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="unexpected root"):
        gallica.document("bpt6k1").page(1).alto()


def test_image_rejects_empty_success_payload() -> None:
    gallica = Gallica(transport=StaticTransport(_response(b"")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="empty"):
        gallica.document("bpt6k1").page(1).image()


def test_image_rejects_html_success_payload() -> None:
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(b"<!doctype html><html></html>", content_type="text/html")
        )
    )
    with pytest.raises(GallicaResponseError, match="IIIF image returned HTML"):
        gallica.document("bpt6k1").page(1).image()


def test_image_rejects_unknown_non_image_payload() -> None:
    gallica = Gallica(
        transport=StaticTransport(_response(b"this is neither an image nor html"))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="unexpected content type"):
        gallica.document("bpt6k1").page(1).image()


def test_image_accepts_jpeg_signature_without_content_type() -> None:
    payload = b"\xff\xd8\xffpayload"
    gallica = Gallica(transport=StaticTransport(_response(payload)))  # type: ignore[arg-type]
    assert gallica.document("bpt6k1").page(1).image() == payload


def test_text_rejects_empty_success_payload() -> None:
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(b"", url="https://gallica.bnf.fr/ark:/12148/bpt6k1.texteBrut")
        )
    )
    with pytest.raises(GallicaResponseError, match="empty"):
        gallica.document("bpt6k1").text()


def test_text_accepts_legitimate_html_representation() -> None:
    payload = b"<html><body><p>Rappel de votre demande</p><p>OCR text</p></body></html>"
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(
                payload,
                content_type="text/html; charset=utf-8",
                url="https://gallica.bnf.fr/ark:/12148/bpt6k1.texteBrut",
            )
        )
    )
    assert "OCR text" in gallica.document("bpt6k1").text()


def test_text_rejects_altcha_challenge() -> None:
    gallica = Gallica(
        transport=StaticTransport(  # type: ignore[arg-type]
            _response(
                b"<html><body><altcha-widget></altcha-widget></body></html>",
                content_type="text/html",
                url="https://gallica.bnf.fr/services/engine/search/altcha",
            )
        )
    )
    with pytest.raises(GallicaResponseError, match="anti-bot challenge"):
        gallica.document("bpt6k1").text()


def test_sru_rejects_html_root_even_with_http_200() -> None:
    gallica = Gallica(transport=StaticTransport(_response(b"<html><body>error</body></html>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="unexpected XML root"):
        gallica.search("test", maximum_records=1)


def test_pagination_rejects_malformed_and_non_integer_counts() -> None:
    malformed = Gallica(transport=StaticTransport(_response(b"<results>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="not valid XML"):
        malformed.document("bpt6k1").page_count()

    non_integer = Gallica(
        transport=StaticTransport(_response(b"<results><nbVueImages>many</nbVueImages></results>"))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="not an integer"):
        non_integer.document("bpt6k1").page_count()

    missing = Gallica(transport=StaticTransport(_response(b"<results/>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="does not contain"):
        missing.document("bpt6k1").page_count()


def test_content_search_rejects_invalid_count_results() -> None:
    gallica = Gallica(
        transport=StaticTransport(_response(b'<results countResults="not-a-number"/>'))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="countResults"):
        gallica.document("bpt6k1").search_text("test")


def test_content_search_rejects_malformed_geometry_and_score() -> None:
    bad_geometry = b'<results countResults="1"><item><altoid><altoidstring hpos="x" vpos="1" width="2" height="3">ID</altoidstring></altoid></item></results>'
    gallica = Gallica(transport=StaticTransport(_response(bad_geometry)))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="hpos is not an integer"):
        gallica.document("bpt6k1").search_text("test", page=1)

    bad_score = b'<results countResults="1"><item score="nope"><p_id>PAG_1</p_id></item></results>'
    gallica = Gallica(transport=StaticTransport(_response(bad_score)))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="score is not numeric"):
        gallica.document("bpt6k1").search_text("test")


def test_iiif_info_rejects_invalid_json_and_non_object_payloads() -> None:
    malformed = Gallica(
        transport=StaticTransport(_response(b"not-json", content_type="application/json"))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="not valid JSON"):
        malformed.document("bpt6k1").page(1).iiif_info()

    non_object = Gallica(
        transport=StaticTransport(_response(b"[]", content_type="application/json"))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="not a JSON object"):
        non_object.document("bpt6k1").page(1).iiif_info()


def test_iiif_info_requires_dimensions() -> None:
    payload = json.dumps({"width": 1000}).encode()
    gallica = Gallica(
        transport=StaticTransport(_response(payload, content_type="application/json"))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="width/height"):
        gallica.document("bpt6k1").page(1).iiif_info()


def test_issues_rejects_malformed_xml_and_wrong_root() -> None:
    malformed = Gallica(transport=StaticTransport(_response(b"<issues>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="not valid XML"):
        malformed.periodical("cb1").issue(date(1937, 3, 25))

    wrong_root = Gallica(transport=StaticTransport(_response(b"<html/>")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="unexpected root"):
        wrong_root.periodical("cb1").issue(date(1937, 3, 25))

from __future__ import annotations

import httpx
import pytest

from gallica import CATEGORY_CQL_FIELDS, Gallica, GallicaResponseError


class StaticTransport:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str] | None, str]] = []

    def close(self) -> None:
        pass

    def get(self, url: str, *, params=None, bucket: str = "default") -> httpx.Response:
        normalized = dict(params) if params is not None else None
        self.calls.append((url, normalized, bucket))
        return self.response


def _response(content: bytes, *, content_type: str = "application/json") -> httpx.Response:
    return httpx.Response(
        200,
        content=content,
        headers={"Content-Type": content_type},
        request=httpx.Request("GET", "https://gallica.bnf.fr/services/Categories"),
    )


def test_categories_exposes_typed_values_and_cql_mapping() -> None:
    payload = b'''[
      {"howMany": 24839, "value": "provenance", "cleanValue": "bnf.fr", "libelleValue": "Gallica"},
      {"howMany": 22207, "value": "language", "cleanValue": "fre", "libelleValue": ""},
      {"howMany": 20746, "value": "typedoc", "cleanValue": "monographies", "libelleValue": ""}
    ]'''
    transport = StaticTransport(_response(payload))
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    categories = gallica.categories('gallica all "toto"')

    assert categories.query == 'gallica all "toto"'
    assert categories.categories == ("provenance", "language", "typedoc")
    assert len(categories) == 3
    provenance = categories.for_category("provenance")[0]
    assert provenance.approximate_count == 24839
    assert provenance.display_value == "Gallica"
    assert provenance.cql_field == "provenance"
    language = categories.for_category("language")[0]
    assert language.label is None
    assert language.display_value == "fre"
    assert language.cql_field == "dc.language"
    assert categories.for_category("typedoc")[0].cql_field == "dc.type"
    assert CATEGORY_CQL_FIELDS["nqamoyen"] == "ocr.quality"
    assert categories.raw_json == payload.decode()

    assert transport.calls == [
        (
            "https://gallica.bnf.fr/services/Categories",
            {"SRU": '(gallica all "toto")'},
            "default",
        )
    ]


def test_categories_preserves_unknown_categories_without_inventing_cql_mapping() -> None:
    response = _response(b'[{"howMany":1,"value":"future_facet","cleanValue":"x","libelleValue":"X"}]')
    categories = Gallica(transport=StaticTransport(response)).categories("gallica all x")  # type: ignore[arg-type]
    item = categories.values[0]
    assert item.category == "future_facet"
    assert item.cql_field is None
    assert item.display_value == "X"


def test_categories_rejects_invalid_payloads() -> None:
    malformed = Gallica(transport=StaticTransport(_response(b"not-json")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="not valid JSON"):
        malformed.categories("gallica all test")

    object_payload = Gallica(transport=StaticTransport(_response(b"{}")))  # type: ignore[arg-type]
    with pytest.raises(GallicaResponseError, match="not a JSON array"):
        object_payload.categories("gallica all test")

    bad_count = Gallica(
        transport=StaticTransport(
            _response(b'[{"howMany":"many","value":"language","cleanValue":"fre","libelleValue":""}]')
        )  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="howMany"):
        bad_count.categories("gallica all test")

    html = Gallica(
        transport=StaticTransport(_response(b"<html>challenge</html>", content_type="text/html"))  # type: ignore[arg-type]
    )
    with pytest.raises(GallicaResponseError, match="returned HTML"):
        html.categories("gallica all test")


def test_categories_rejects_empty_query() -> None:
    gallica = Gallica(transport=StaticTransport(_response(b"[]")))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must not be empty"):
        gallica.categories("   ")

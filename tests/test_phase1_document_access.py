from __future__ import annotations

from datetime import date

import httpx

from gallica import Gallica


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str] | None, str]] = []

    def close(self) -> None:
        pass

    def get(self, url: str, *, params=None, bucket: str = "default") -> httpx.Response:
        normalized = dict(params) if params is not None else None
        self.calls.append((url, normalized, bucket))
        request = httpx.Request("GET", url, params=params)
        if url.endswith(".texteBrut"):
            return httpx.Response(200, text="OCR text", request=request)
        if url.endswith("/services/ContentSearch"):
            xml = """<results countResults="1"><query>hugo</query><items><item score="0.75"><altoid>A1</altoid><p_id>PAG_357</p_id><content>HUGO</content></item></items></results>"""
            return httpx.Response(200, text=xml, request=request)
        if url.endswith("/services/Issues"):
            xml = b'<issues><issue ark="ark:/12148/bpt6k5509212w" dayOfYear="84"/></issues>'
            return httpx.Response(200, content=xml, request=request)
        raise AssertionError(f"Unexpected URL: {url}")


def test_document_and_page_text_use_text_rate_bucket() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]
    doc = gallica.document("bpt6k5460422k")

    assert doc.text() == "OCR text"
    assert transport.calls[-1][0].endswith("bpt6k5460422k.texteBrut")
    assert transport.calls[-1][2] == "text"

    assert doc.page(3).text() == "OCR text"
    assert transport.calls[-1][0].endswith("bpt6k5460422k/f3n1.texteBrut")
    assert transport.calls[-1][2] == "text"


def test_content_search_preserves_parameters_and_parses_items() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    result = gallica.document("bpt6k5460422k").search_text("hugo", page=2, start_result=11)
    assert result.total == 1
    assert result.query == "hugo"
    assert result.items[0].page_id == "PAG_357"
    assert result.items[0].content_html == "HUGO"
    assert result.items[0].alto_id == "A1"
    assert result.items[0].score == 0.75
    assert "countResults" in result.raw_xml
    _, params, _ = transport.calls[-1]
    assert params == {"ark": "bpt6k5460422k", "query": "hugo", "page": "2", "startResult": "11"}


def test_periodical_resolves_day_of_year_to_document() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    issue = gallica.periodical("cb32798952c").issue(date(1937, 3, 25))
    assert issue is not None
    assert issue.ark == "bpt6k5509212w"
    _, params, _ = transport.calls[-1]
    assert params == {"ark": "ark:/12148/cb32798952c/date", "date": "1937"}

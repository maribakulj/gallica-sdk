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
            page = normalized.get("page") if normalized is not None else None
            start_result = normalized.get("startResult") if normalized is not None else None
            query = normalized.get("query") if normalized is not None else None
            if page is not None:
                xml = """<results countResults="1"><query>hugo</query><items><item score="0.75"><altoid countResults="2"><altoidstring height="47" hpos="514" vpos="915" width="101">PAG_00000173_ST000061</altoidstring><altoidstring height="48" hpos="700" vpos="920" width="110">PAG_00000173_ST000062</altoidstring></altoid><p_id>PAG_173</p_id><p_width>1153</p_width><p_height>2138</p_height><content/></item></items></results>"""
                return httpx.Response(200, text=xml, request=request)
            if query == "paginate":
                start = int(start_result or "1")
                if start == 1:
                    items = "".join(
                        f"<item><altoid/><p_id>PAG_{index}</p_id><p_width/><p_height/><content>hit {index}</content></item>"
                        for index in range(1, 11)
                    )
                elif start == 11:
                    items = "".join(
                        f"<item><altoid/><p_id>PAG_{index}</p_id><p_width/><p_height/><content>hit {index}</content></item>"
                        for index in range(11, 13)
                    )
                else:
                    items = ""
                xml = f'<results countResults="12"><query>paginate</query><items>{items}</items></results>'
                return httpx.Response(200, text=xml, request=request)
            xml = """<results countResults="1"><query>hugo</query><items><item score="0.75"><altoid>A1</altoid><p_id>PAG_357</p_id><p_width/><p_height/><content>HUGO</content></item></items></results>"""
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


def test_content_search_preserves_legacy_alto_id_and_parameters() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    result = gallica.document("bpt6k5460422k").search_text("hugo", start_result=1)
    assert result.total == 1
    assert result.query == "hugo"
    assert result.items[0].page_id == "PAG_357"
    assert result.items[0].content_html == "HUGO"
    assert result.items[0].alto_id == "A1"
    assert result.items[0].matches == ()
    assert result.items[0].score == 0.75
    assert "countResults" in result.raw_xml
    _, params, _ = transport.calls[-1]
    assert params == {"ark": "bpt6k5460422k", "query": "hugo", "startResult": "1"}


def test_content_search_page_parses_master_dimensions_and_all_word_rectangles() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    result = gallica.document("bpt6k5460422k").search_text("hugo", page=173)
    item = result.items[0]
    assert item.page_id == "PAG_173"
    assert item.page_width == 1153
    assert item.page_height == 2138
    assert item.alto_id == "PAG_00000173_ST000061"
    assert len(item.matches) == 2
    assert item.matches[0].hpos == 514
    assert item.matches[0].vpos == 915
    assert item.matches[0].width == 101
    assert item.matches[0].height == 47
    assert item.matches[1].alto_id == "PAG_00000173_ST000062"


def test_content_search_all_paginates_lazily_and_respects_limit() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]
    doc = gallica.document("bpt6k5460422k")

    all_items = list(doc.search_text_all("paginate"))
    assert len(all_items) == 12
    starts = [call[1]["startResult"] for call in transport.calls if call[1] is not None]
    assert starts == ["1", "11"]

    transport.calls.clear()
    limited = list(doc.search_text_all("paginate", limit=3))
    assert len(limited) == 3
    starts = [call[1]["startResult"] for call in transport.calls if call[1] is not None]
    assert starts == ["1"]


def test_periodical_resolves_day_of_year_to_document() -> None:
    transport = FakeTransport()
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    issue = gallica.periodical("cb32798952c").issue(date(1937, 3, 25))
    assert issue is not None
    assert issue.ark == "bpt6k5509212w"
    _, params, _ = transport.calls[-1]
    assert params == {"ark": "ark:/12148/cb32798952c/date", "date": "1937"}

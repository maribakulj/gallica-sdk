from __future__ import annotations

import json
from typing import Self

import pytest

from gallica import cli
from gallica.models import (
    Categories,
    CategoryValue,
    DocumentMetadata,
    DublinCoreRecord,
    IIIFImageInfo,
    IIIFPresentationManifest,
    Pagination,
    PaginationPage,
    SearchResults,
    TocDocument,
)


def test_capabilities_command_emits_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["capabilities"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert any(item["id"] == "page_alto" for item in payload)


def test_contract_command_resolves_one_capability(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["contract", "page_alto"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "page_alto"
    assert payload["call"] == "Page.alto"
    assert payload["services"]


def test_unknown_contract_is_a_cli_error() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["contract", "definitely_missing"])
    assert exc.value.code == 2


def test_search_limit_is_bounded() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["search", "gallica all test", "--limit", "51"])
    assert exc.value.code == 2


def test_iiif_info_view_is_positive() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["iiif-info", "bpt6ktest", "0"])
    assert exc.value.code == 2


def test_network_commands_delegate_to_sdk(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    record = DublinCoreRecord(
        fields={
            "title": ("Example",),
            "identifier": ("https://gallica.bnf.fr/ark:/12148/bpt6ktest",),
        }
    )
    metadata = DocumentMetadata(
        ark="bpt6ktest",
        record=record,
        indexing_mode="OCR",
        ocr_quality=0.99,
        raw_xml="<record />",
    )
    categories = Categories(
        query="gallica all test",
        values=(
            CategoryValue(
                category="language",
                clean_value="fre",
                approximate_count=12,
                label="Français",
            ),
        ),
        raw_json="[]",
    )
    pagination = Pagination(
        first_displayed_page=2,
        has_toc=True,
        toc_location=9,
        has_content=True,
        digital_id="bpt6ktest",
        image_views=12,
        audio_views=None,
        pages=(PaginationPage(number="1", order=2, pagination_type="PAGE"),),
        raw_xml="<livre />",
    )
    toc = TocDocument(format="tei", raw="<TEI />", well_formed=True)
    manifest = IIIFPresentationManifest(
        version="2",
        identifier="https://example.test/manifest",
        context=("http://iiif.io/api/presentation/2/context.json",),
        canvas_count=12,
        raw_json="{}",
    )
    info = IIIFImageInfo(
        version="unknown",
        identifier=None,
        context=(),
        protocol=None,
        profiles=(),
        width=10784,
        height=7200,
        raw_json="{}",
    )

    class FakePage:
        def iiif_info(self) -> IIIFImageInfo:
            return info

    class FakeDocument:
        ark = "bpt6ktest"

        def metadata(self) -> DocumentMetadata:
            return metadata

        def page_count(self) -> int:
            return 12

        def pagination(self) -> Pagination:
            return pagination

        def toc(self) -> TocDocument:
            return toc

        def iiif_manifest(self) -> IIIFPresentationManifest:
            return manifest

        def page(self, number: int) -> FakePage:
            assert number == 3
            return FakePage()

    class FakeGallica:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def search(self, query: str, *, start_record: int, maximum_records: int) -> SearchResults:
            assert start_record == 1
            assert maximum_records == 3
            return SearchResults(query=query, total=1, records=(record,), raw_xml="<search />")

        def categories(self, query: str) -> Categories:
            assert query == "gallica all test"
            return categories

        def document(self, ark: str) -> FakeDocument:
            assert ark == "bpt6ktest"
            return FakeDocument()

    monkeypatch.setattr(cli, "Gallica", FakeGallica)

    assert cli.main(["search", "gallica all test", "--limit", "3"]) == 0
    search_payload = json.loads(capsys.readouterr().out)
    assert search_payload["records"][0]["ark"] == "bpt6ktest"

    assert cli.main(["categories", "gallica all test"]) == 0
    categories_payload = json.loads(capsys.readouterr().out)
    assert categories_payload["categories"] == ["language"]
    assert categories_payload["values"][0]["cql_field"] == "dc.language"
    assert categories_payload["values"][0]["approximate_count"] == 12

    assert cli.main(["metadata", "bpt6ktest"]) == 0
    metadata_payload = json.loads(capsys.readouterr().out)
    assert metadata_payload["record"]["fields"]["title"] == ["Example"]

    assert cli.main(["page-count", "bpt6ktest"]) == 0
    page_payload = json.loads(capsys.readouterr().out)
    assert page_payload == {"ark": "bpt6ktest", "page_count": 12}

    assert cli.main(["pagination", "bpt6ktest"]) == 0
    pagination_payload = json.loads(capsys.readouterr().out)
    assert pagination_payload["image_views"] == 12
    assert pagination_payload["pages"][0]["order"] == 2

    assert cli.main(["toc", "bpt6ktest"]) == 0
    toc_payload = json.loads(capsys.readouterr().out)
    assert toc_payload["format"] == "tei"
    assert toc_payload["raw"] == "<TEI />"

    assert cli.main(["iiif-manifest", "bpt6ktest"]) == 0
    manifest_payload = json.loads(capsys.readouterr().out)
    assert manifest_payload["version"] == "2"
    assert manifest_payload["canvas_count"] == 12
    assert "raw_json" not in manifest_payload

    assert cli.main(["iiif-info", "bpt6ktest", "3"]) == 0
    info_payload = json.loads(capsys.readouterr().out)
    assert info_payload["view"] == 3
    assert info_payload["version"] == "unknown"
    assert info_payload["width"] == 10784
    assert "raw_json" not in info_payload

from __future__ import annotations

import json

import pytest

from gallica import cli
from gallica.models import DocumentMetadata, DublinCoreRecord, SearchResults


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

    class FakeDocument:
        ark = "bpt6ktest"

        def metadata(self) -> DocumentMetadata:
            return metadata

        def page_count(self) -> int:
            return 12

    class FakeGallica:
        def __enter__(self) -> "FakeGallica":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def search(self, query: str, *, start_record: int, maximum_records: int) -> SearchResults:
            assert start_record == 1
            assert maximum_records == 3
            return SearchResults(query=query, total=1, records=(record,), raw_xml="<search />")

        def document(self, ark: str) -> FakeDocument:
            assert ark == "bpt6ktest"
            return FakeDocument()

    monkeypatch.setattr(cli, "Gallica", FakeGallica)

    assert cli.main(["search", "gallica all test", "--limit", "3"]) == 0
    search_payload = json.loads(capsys.readouterr().out)
    assert search_payload["records"][0]["ark"] == "bpt6ktest"

    assert cli.main(["metadata", "bpt6ktest"]) == 0
    metadata_payload = json.loads(capsys.readouterr().out)
    assert metadata_payload["record"]["fields"]["title"] == ["Example"]

    assert cli.main(["page-count", "bpt6ktest"]) == 0
    page_payload = json.loads(capsys.readouterr().out)
    assert page_payload == {"ark": "bpt6ktest", "page_count": 12}

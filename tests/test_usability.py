from __future__ import annotations

import json
from pathlib import Path

from gallica import Gallica
from gallica.models import DublinCoreRecord, SearchResults


def _record(ark: str) -> DublinCoreRecord:
    return DublinCoreRecord(
        fields={
            "title": (f"Title {ark}",),
            "identifier": (f"https://gallica.bnf.fr/ark:/12148/{ark}",),
        }
    )


class FakePagedGallica(Gallica):
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def close(self) -> None:
        pass

    def search(
        self,
        query: str,
        *,
        start_record: int = 1,
        maximum_records: int = 50,
    ) -> SearchResults:
        self.calls.append((start_record, maximum_records))
        all_records = tuple(_record(f"bpt6k{i}") for i in range(1, 6))
        start = start_record - 1
        records = all_records[start : start + maximum_records]
        return SearchResults(query=query, total=len(all_records), records=records, raw_xml="<sru/>")


def test_search_all_paginates_lazily_and_respects_limit() -> None:
    gallica = FakePagedGallica()
    records = list(gallica.search_all("x", limit=4, page_size=2))
    assert [record.ark for record in records] == ["bpt6k1", "bpt6k2", "bpt6k3", "bpt6k4"]
    assert gallica.calls == [(1, 2), (3, 2)]


def test_search_all_stops_at_total() -> None:
    gallica = FakePagedGallica()
    records = list(gallica.search_all("x", page_size=3))
    assert len(records) == 5
    assert gallica.calls == [(1, 3), (4, 3)]


def test_search_results_arks_and_jsonl(tmp_path: Path) -> None:
    results = SearchResults(
        query="x",
        total=2,
        records=(_record("bpt6k1"), _record("bpt6k2")),
        raw_xml="<sru/>",
    )
    assert results.arks == ("bpt6k1", "bpt6k2")
    path = results.write_jsonl(tmp_path / "nested" / "records.jsonl")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["ark"] == "bpt6k1"
    assert first["fields"]["title"] == ["Title bpt6k1"]


def test_search_all_validates_arguments() -> None:
    gallica = FakePagedGallica()
    for kwargs in ({"limit": 0}, {"page_size": 0}, {"page_size": 51}):
        try:
            list(gallica.search_all("x", **kwargs))  # type: ignore[arg-type]
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid arguments accepted: {kwargs}")

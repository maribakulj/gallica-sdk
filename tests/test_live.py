from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from gallica import Gallica, GallicaResponseError

pytestmark = pytest.mark.live


def test_public_gallica_vertical_slice() -> None:
    with Gallica() as gallica:
        results = gallica.search('gallica all "Verdun"', maximum_records=1)
        assert results.total > 0
        assert len(results) == 1
        assert results.records[0].title is not None
        assert results.records[0].ark is not None
        assert "searchRetrieveResponse" in results.raw_xml

        doc = gallica.document("bpt6k5738219s")
        assert doc.page_count() == 374
        metadata = doc.metadata()
        assert metadata.ark == "bpt6k5738219s"
        assert metadata.record.identifiers
        assert "results" in metadata.raw_xml

        alto = gallica.document("bpt6k5619759j").page(3).alto()
        assert len(alto) > 1000

        info = gallica.document("btv1b53066668g").page(1).iiif_info()
        assert int(info["width"]) > 1000

        image = gallica.document("btv1b53066668g").page(1).image(width=1000)
        assert len(image) > 1000


def test_public_gallica_phase1_document_access() -> None:
    with Gallica() as gallica:
        text_doc = gallica.document("bpt6k5460422k")
        try:
            text = text_doc.text()
        except GallicaResponseError as exc:
            # Public cold runners are currently redirected to Gallica's anti-bot
            # challenge. Detecting that response is the expected safe behavior.
            assert "anti-bot challenge" in str(exc)
        else:
            assert len(text) > 100
            assert len(text_doc.page(1).text()) > 10

        search = text_doc.search_text("hugo", start_result=1)
        assert search.total >= 1
        assert len(search) >= 1
        assert search.items[0].page_id is not None
        assert search.items[0].content_html is not None
        assert "results" in search.raw_xml.lower()

        geometry = text_doc.search_text("hugo", page=173)
        assert geometry.total == 1
        assert len(geometry.items) == 1
        geometry_item = geometry.items[0]
        assert geometry_item.page_id == "PAG_173"
        assert geometry_item.page_width == 1153
        assert geometry_item.page_height == 2138
        assert geometry_item.matches
        assert geometry_item.matches[0].alto_id
        assert geometry_item.matches[0].width > 0
        assert geometry_item.matches[0].height > 0

        lazy_items = list(text_doc.search_text_all("hugo", limit=3))
        assert len(lazy_items) == 3
        assert all(item.page_id is not None for item in lazy_items)

        issue = gallica.periodical("cb32798952c").issue(date(1937, 3, 25))
        assert issue is not None
        assert issue.ark == "bpt6k5509212w"


def test_public_gallica_corpus_v1(tmp_path: Path) -> None:
    with Gallica() as gallica:
        corpus = gallica.corpus(["ark:/12148/bpt6k5460422k", "bpt6k5460422k"])
        assert len(corpus) == 1

        # texteBrut is environment-limited on public cold runners, so this live
        # corpus contract validates metadata + provenance-aware resume. Page-level
        # ALTO/image artifacts are covered separately below.
        report = corpus.fetch(tmp_path, metadata=True, text=False, resume=True)
        assert len(report.successes) == 1
        assert not report.failures

        document_dir = tmp_path / "documents" / "bpt6k5460422k"
        metadata = json.loads((document_dir / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["ark"] == "bpt6k5460422k"
        assert metadata["fields"]

        second = corpus.fetch(tmp_path, metadata=True, text=False, resume=True)
        assert len(second.skipped) == 1
        assert len((tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_public_gallica_corpus_page_artifacts(tmp_path: Path) -> None:
    with Gallica() as gallica:
        corpus = gallica.corpus(["bpt6k5619759j"])
        report = corpus.fetch(
            tmp_path,
            metadata=False,
            alto=True,
            images=True,
            views=[3],
            image_width=800,
            resume=True,
        )
        assert len(report.successes) == 1
        page_dir = tmp_path / "documents" / "bpt6k5619759j" / "pages" / "3"
        assert len((page_dir / "alto.xml").read_bytes()) > 1000
        assert len((page_dir / "image.jpg").read_bytes()) > 1000

        second = corpus.fetch(
            tmp_path,
            metadata=False,
            alto=True,
            images=True,
            views=[3],
            image_width=800,
            resume=True,
        )
        assert len(second.skipped) == 1

from __future__ import annotations

import json
from pathlib import Path

from gallica.corpus import Corpus
from gallica.models import DocumentMetadata, DublinCoreRecord


class FakeDocument:
    def __init__(self, ark: str, calls: list[tuple[str, str]]) -> None:
        self.ark = ark
        self.calls = calls

    def metadata(self) -> DocumentMetadata:
        self.calls.append((self.ark, "metadata"))
        if self.ark == "badark":
            raise RuntimeError("metadata unavailable")
        return DocumentMetadata(
            ark=self.ark,
            record=DublinCoreRecord(
                fields={"title": (f"Title {self.ark}",), "identifier": (f"https://gallica.bnf.fr/ark:/12148/{self.ark}",)}
            ),
            indexing_mode="OCR",
            ocr_quality=95.0,
            raw_xml="<results/>",
        )

    def text(self) -> str:
        self.calls.append((self.ark, "text"))
        return f"Text for {self.ark}"


class FakeGallica:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def document(self, ark: str) -> FakeDocument:
        return FakeDocument(ark, self.calls)


def test_corpus_normalizes_and_deduplicates_arks() -> None:
    corpus = Corpus(FakeGallica(), ["ark:/12148/bpt6k1", "bpt6k1", "bpt6k2"])  # type: ignore[arg-type]
    assert corpus.arks == ("bpt6k1", "bpt6k2")


def test_corpus_fetch_writes_manifest_and_resumes(tmp_path: Path) -> None:
    gallica = FakeGallica()
    corpus = Corpus(gallica, ["bpt6k1", "bpt6k2"])  # type: ignore[arg-type]

    first = corpus.fetch(tmp_path, metadata=True, text=True)
    assert len(first.successes) == 2
    assert not first.failures
    assert (tmp_path / "documents" / "bpt6k1" / "metadata.json").is_file()
    assert (tmp_path / "documents" / "bpt6k1" / "text.txt").read_text(encoding="utf-8") == "Text for bpt6k1"

    metadata = json.loads((tmp_path / "documents" / "bpt6k1" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["fields"]["title"] == ["Title bpt6k1"]

    manifest_lines = (tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(manifest_lines) == 2
    assert json.loads(manifest_lines[0])["status"] == "success"

    call_count = len(gallica.calls)
    second = corpus.fetch(tmp_path, metadata=True, text=True, resume=True)
    assert len(second.skipped) == 2
    assert len(gallica.calls) == call_count
    assert len((tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_corpus_resume_fetches_only_missing_artifact(tmp_path: Path) -> None:
    gallica = FakeGallica()
    corpus = Corpus(gallica, ["bpt6k1"])  # type: ignore[arg-type]
    corpus.fetch(tmp_path, metadata=True, text=False)
    gallica.calls.clear()

    report = corpus.fetch(tmp_path, metadata=True, text=True, resume=True)
    assert report.items[0].status == "success"
    assert gallica.calls == [("bpt6k1", "text")]


def test_corpus_failure_does_not_stop_following_arks(tmp_path: Path) -> None:
    gallica = FakeGallica()
    corpus = Corpus(gallica, ["badark", "bpt6k2"])  # type: ignore[arg-type]

    report = corpus.fetch(tmp_path, metadata=True)
    assert len(report.failures) == 1
    assert report.failures[0].ark == "badark"
    assert "RuntimeError" in (report.failures[0].error or "")
    assert len(report.successes) == 1
    assert report.successes[0].ark == "bpt6k2"
    assert (tmp_path / "documents" / "bpt6k2" / "metadata.json").is_file()


def test_corpus_requires_at_least_one_artifact(tmp_path: Path) -> None:
    corpus = Corpus(FakeGallica(), ["bpt6k1"])  # type: ignore[arg-type]
    try:
        corpus.fetch(tmp_path, metadata=False, text=False)
    except ValueError as exc:
        assert "at least one artifact" in str(exc)
    else:
        raise AssertionError("empty corpus fetch should be rejected")

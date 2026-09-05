from __future__ import annotations

from pathlib import Path

import httpx

from gallica.corpus import Corpus
from gallica.models import DocumentMetadata, DublinCoreRecord


def _metadata(ark: str) -> DocumentMetadata:
    return DocumentMetadata(
        ark=ark,
        record=DublinCoreRecord(
            fields={
                "title": (f"Title {ark}",),
                "identifier": (f"https://gallica.bnf.fr/ark:/12148/{ark}",),
            }
        ),
        indexing_mode="OCR",
        ocr_quality=95.0,
        raw_xml="<results/>",
    )


class MetadataFailureDocument:
    def __init__(self, ark: str, calls: list[str]) -> None:
        self.ark = ark
        self.calls = calls

    def metadata(self) -> DocumentMetadata:
        self.calls.append("metadata")
        raise ValueError("metadata malformed")

    def text(self) -> str:
        self.calls.append("text")
        return "usable OCR text"


class MetadataFailureGallica:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def document(self, ark: str) -> MetadataFailureDocument:
        return MetadataFailureDocument(ark, self.calls)


class FlakyTextDocument:
    def __init__(self, ark: str, owner: FlakyTextGallica) -> None:
        self.ark = ark
        self.owner = owner

    def metadata(self) -> DocumentMetadata:
        self.owner.calls.append("metadata")
        return _metadata(self.ark)

    def text(self) -> str:
        self.owner.calls.append("text")
        if self.owner.fail_text:
            request = httpx.Request("GET", "https://gallica.bnf.fr/ark:/12148/example.texteBrut")
            raise httpx.ConnectError("temporary connection failure", request=request)
        return "OCR recovered on retry"


class FlakyTextGallica:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail_text = True

    def document(self, ark: str) -> FlakyTextDocument:
        return FlakyTextDocument(ark, self)


def test_failure_of_one_artifact_does_not_hide_later_artifacts(tmp_path: Path) -> None:
    gallica = MetadataFailureGallica()
    corpus = Corpus(gallica, ["bpt6k1"])  # type: ignore[arg-type]

    report = corpus.fetch(tmp_path, metadata=True, text=True)

    assert len(report.failures) == 1
    item = report.failures[0]
    assert item.status == "error"
    assert item.metadata_path is None
    assert item.text_path is not None
    assert Path(item.text_path).read_text(encoding="utf-8") == "usable OCR text"
    assert gallica.calls == ["metadata", "text"]
    assert len(item.artifacts) == 1
    assert item.artifacts[0].kind == "text"
    assert len(item.failure_details) == 1
    failure = item.failure_details[0]
    assert failure.kind == "metadata"
    assert failure.error_type == "ValueError"
    assert failure.message == "metadata malformed"
    assert failure.retryable is False
    assert item.retryable is False
    assert "metadata: ValueError" in (item.error or "")


def test_resume_reuses_successes_and_retries_only_failed_artifacts(tmp_path: Path) -> None:
    gallica = FlakyTextGallica()
    corpus = Corpus(gallica, ["bpt6k1"])  # type: ignore[arg-type]

    first = corpus.fetch(tmp_path, metadata=True, text=True, resume=True)
    assert len(first.failures) == 1
    assert first.failures[0].retryable is True
    assert len(first.retryable) == 1
    assert [record.kind for record in first.failures[0].artifacts] == ["metadata"]
    assert gallica.calls == ["metadata", "text"]

    gallica.calls.clear()
    gallica.fail_text = False
    second = corpus.fetch(tmp_path, metadata=True, text=True, resume=True)

    assert len(second.successes) == 1
    assert not second.failures
    assert gallica.calls == ["text"]
    assert {record.kind for record in second.successes[0].artifacts} == {"metadata", "text"}


def test_http_status_failure_classifies_only_transient_statuses_as_retryable(tmp_path: Path) -> None:
    class StatusDocument:
        def __init__(self, status: int) -> None:
            self.status = status

        def metadata(self) -> DocumentMetadata:
            request = httpx.Request("GET", "https://gallica.bnf.fr/services/OAIRecord")
            response = httpx.Response(self.status, request=request)
            raise httpx.HTTPStatusError("status failure", request=request, response=response)

    class StatusGallica:
        def __init__(self, status: int) -> None:
            self.status = status

        def document(self, ark: str) -> StatusDocument:
            return StatusDocument(self.status)

    transient = Corpus(StatusGallica(503), ["bpt6k1"])  # type: ignore[arg-type]
    permanent = Corpus(StatusGallica(404), ["bpt6k2"])  # type: ignore[arg-type]

    assert transient.fetch(tmp_path / "transient", metadata=True).failures[0].retryable is True
    assert permanent.fetch(tmp_path / "permanent", metadata=True).failures[0].retryable is False

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from gallica.corpus import Corpus
from gallica.models import DocumentMetadata, DublinCoreRecord


class FakePage:
    def __init__(self, ark: str, number: int, calls: list[tuple[str, str]]) -> None:
        self.ark = ark
        self.number = number
        self.calls = calls

    def alto(self) -> bytes:
        self.calls.append((self.ark, f"alto:{self.number}"))
        return f"<alto view='{self.number}'/>".encode()

    def image(self, *, width: int = 1000, fmt: str = "jpg") -> bytes:
        self.calls.append((self.ark, f"image:{self.number}:{width}:{fmt}"))
        return f"JPEG {self.number} {width}".encode()


class FakeDocument:
    def __init__(self, ark: str, calls: list[tuple[str, str]]) -> None:
        self.ark = ark
        self.calls = calls

    def metadata(self) -> DocumentMetadata:
        self.calls.append((self.ark, "metadata"))
        return DocumentMetadata(
            ark=self.ark,
            record=DublinCoreRecord(
                fields={
                    "title": (f"Title {self.ark}",),
                    "identifier": (f"https://gallica.bnf.fr/ark:/12148/{self.ark}",),
                }
            ),
            indexing_mode="OCR",
            ocr_quality=95.0,
            raw_xml="<results/>",
        )

    def text(self) -> str:
        self.calls.append((self.ark, "text"))
        return f"Text for {self.ark}"

    def page(self, number: int) -> FakePage:
        return FakePage(self.ark, number, self.calls)


class FakeGallica:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def document(self, ark: str) -> FakeDocument:
        return FakeDocument(ark, self.calls)


def test_manifest_records_artifact_provenance(tmp_path: Path) -> None:
    gallica = FakeGallica()
    corpus = Corpus(gallica, ["bpt6k1"])  # type: ignore[arg-type]

    report = corpus.fetch(tmp_path, metadata=True, text=True)
    item = report.successes[0]
    assert {artifact.kind for artifact in item.artifacts} == {"metadata", "text"}

    manifest_item = json.loads((tmp_path / "manifest.jsonl").read_text(encoding="utf-8"))
    artifacts = manifest_item["artifacts"]
    assert len(artifacts) == 2
    for artifact in artifacts:
        path = tmp_path / artifact["path"]
        content = path.read_bytes()
        assert artifact["size"] == len(content)
        assert artifact["sha256"] == hashlib.sha256(content).hexdigest()
        assert len(artifact["fingerprint"]) == 64
        assert artifact["sdk_version"]


def test_resume_refetches_image_when_width_changes(tmp_path: Path) -> None:
    gallica = FakeGallica()
    corpus = Corpus(gallica, ["bpt6k1"])  # type: ignore[arg-type]

    corpus.fetch(
        tmp_path,
        metadata=False,
        images=True,
        views=[1],
        image_width=800,
    )
    gallica.calls.clear()

    report = corpus.fetch(
        tmp_path,
        metadata=False,
        images=True,
        views=[1],
        image_width=1000,
        resume=True,
    )
    assert len(report.successes) == 1
    assert not report.skipped
    assert gallica.calls == [("bpt6k1", "image:1:1000:jpg")]
    image_path = tmp_path / "documents" / "bpt6k1" / "pages" / "1" / "image.jpg"
    assert image_path.read_bytes() == b"JPEG 1 1000"


def test_resume_refetches_corrupted_artifact(tmp_path: Path) -> None:
    gallica = FakeGallica()
    corpus = Corpus(gallica, ["bpt6k1"])  # type: ignore[arg-type]

    corpus.fetch(tmp_path, metadata=False, text=True)
    text_path = tmp_path / "documents" / "bpt6k1" / "text.txt"
    text_path.write_text("corrupted", encoding="utf-8")
    gallica.calls.clear()

    report = corpus.fetch(tmp_path, metadata=False, text=True, resume=True)
    assert len(report.successes) == 1
    assert gallica.calls == [("bpt6k1", "text")]
    assert text_path.read_text(encoding="utf-8") == "Text for bpt6k1"


def test_legacy_manifest_without_artifact_provenance_is_not_trusted(tmp_path: Path) -> None:
    document_dir = tmp_path / "documents" / "bpt6k1"
    document_dir.mkdir(parents=True)
    (document_dir / "text.txt").write_text("legacy text", encoding="utf-8")
    (tmp_path / "manifest.jsonl").write_text(
        json.dumps(
            {
                "ark": "bpt6k1",
                "status": "success",
                "text_path": str(document_dir / "text.txt"),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    gallica = FakeGallica()
    corpus = Corpus(gallica, ["bpt6k1"])  # type: ignore[arg-type]
    report = corpus.fetch(tmp_path, metadata=False, text=True, resume=True)

    assert len(report.successes) == 1
    assert gallica.calls == [("bpt6k1", "text")]
    assert (document_dir / "text.txt").read_text(encoding="utf-8") == "Text for bpt6k1"

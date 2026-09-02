from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from .ark import normalize_ark

if TYPE_CHECKING:
    from .client import Gallica

CorpusStatus = Literal["success", "error", "skipped"]


@dataclass(frozen=True, slots=True)
class CorpusItemResult:
    ark: str
    status: CorpusStatus
    metadata_path: str | None = None
    text_path: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CorpusReport:
    items: tuple[CorpusItemResult, ...]
    manifest_path: str

    def __iter__(self) -> Iterator[CorpusItemResult]:
        return iter(self.items)

    @property
    def successes(self) -> tuple[CorpusItemResult, ...]:
        return tuple(item for item in self.items if item.status == "success")

    @property
    def failures(self) -> tuple[CorpusItemResult, ...]:
        return tuple(item for item in self.items if item.status == "error")

    @property
    def skipped(self) -> tuple[CorpusItemResult, ...]:
        return tuple(item for item in self.items if item.status == "skipped")


class Corpus:
    """A small, resumable collection of Gallica documents.

    V1 deliberately stays synchronous. Network throttling belongs to the shared
    Gallica transport, so corpus execution cannot accidentally bypass per-service
    rate limits by inventing its own request layer.
    """

    def __init__(self, gallica: Gallica, arks: Iterable[str]) -> None:
        self._gallica = gallica
        seen: set[str] = set()
        normalized: list[str] = []
        for value in arks:
            ark = normalize_ark(value)
            if ark not in seen:
                seen.add(ark)
                normalized.append(ark)
        self.arks = tuple(normalized)

    def __len__(self) -> int:
        return len(self.arks)

    def __iter__(self) -> Iterator[str]:
        return iter(self.arks)

    @staticmethod
    def _write_atomic(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)

    @staticmethod
    def _append_manifest(path: Path, item: CorpusItemResult) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True))
            stream.write("\n")

    @staticmethod
    def _metadata_json(metadata: object) -> str:
        # DocumentMetadata is intentionally serialized through its public shape,
        # not pickle or an internal implementation-specific representation.
        from .models import DocumentMetadata

        if not isinstance(metadata, DocumentMetadata):
            raise TypeError("metadata must be a DocumentMetadata instance")
        payload = {
            "ark": metadata.ark,
            "indexing_mode": metadata.indexing_mode,
            "ocr_quality": metadata.ocr_quality,
            "fields": {key: list(values) for key, values in metadata.record.fields.items()},
        }
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def fetch(
        self,
        output: str | Path,
        *,
        metadata: bool = True,
        text: bool = False,
        resume: bool = True,
    ) -> CorpusReport:
        """Fetch selected artifacts for every ARK and return an execution report.

        Successful and failed attempts are appended to ``manifest.jsonl``.
        With ``resume=True``, an ARK is skipped only when every requested artifact
        is already present. Partially completed ARKs fetch only the missing files.
        """
        if not metadata and not text:
            raise ValueError("at least one artifact must be requested")

        root = Path(output)
        manifest = root / "manifest.jsonl"
        results: list[CorpusItemResult] = []

        for ark in self.arks:
            document_dir = root / "documents" / ark
            metadata_file = document_dir / "metadata.json"
            text_file = document_dir / "text.txt"
            requested_paths = [
                path
                for enabled, path in ((metadata, metadata_file), (text, text_file))
                if enabled
            ]

            if resume and requested_paths and all(path.is_file() for path in requested_paths):
                results.append(
                    CorpusItemResult(
                        ark=ark,
                        status="skipped",
                        metadata_path=str(metadata_file) if metadata else None,
                        text_path=str(text_file) if text else None,
                    )
                )
                continue

            try:
                doc = self._gallica.document(ark)
                if metadata and not (resume and metadata_file.is_file()):
                    self._write_atomic(metadata_file, self._metadata_json(doc.metadata()))
                if text and not (resume and text_file.is_file()):
                    self._write_atomic(text_file, doc.text())
                item = CorpusItemResult(
                    ark=ark,
                    status="success",
                    metadata_path=str(metadata_file) if metadata else None,
                    text_path=str(text_file) if text else None,
                )
            except Exception as exc:  # noqa: BLE001 - per-item failure isolation is the contract
                item = CorpusItemResult(
                    ark=ark,
                    status="error",
                    metadata_path=str(metadata_file) if metadata and metadata_file.is_file() else None,
                    text_path=str(text_file) if text and text_file.is_file() else None,
                    error=f"{type(exc).__name__}: {exc}",
                )
            self._append_manifest(manifest, item)
            results.append(item)

        return CorpusReport(items=tuple(results), manifest_path=str(manifest))

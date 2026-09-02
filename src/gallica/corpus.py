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
    alto_paths: tuple[str, ...] = ()
    image_paths: tuple[str, ...] = ()
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

    Corpus stays synchronous and delegates every network operation to normal SDK
    primitives so central throttling and retry policies remain authoritative.
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
    def _normalize_views(views: Iterable[int] | None) -> tuple[int, ...]:
        if views is None:
            return ()
        seen: set[int] = set()
        normalized: list[int] = []
        for view in views:
            if view < 1:
                raise ValueError("views must contain only integers >= 1")
            if view not in seen:
                seen.add(view)
                normalized.append(view)
        return tuple(normalized)

    @staticmethod
    def _write_atomic(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)

    @staticmethod
    def _write_atomic_bytes(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_bytes(content)
        os.replace(temporary, path)

    @staticmethod
    def _append_manifest(path: Path, item: CorpusItemResult) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True))
            stream.write("\n")

    @staticmethod
    def _metadata_json(metadata: object) -> str:
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
        alto: bool = False,
        images: bool = False,
        views: Iterable[int] | None = None,
        image_width: int = 1000,
        resume: bool = True,
    ) -> CorpusReport:
        """Fetch selected artifacts for every ARK and return an execution report.

        Page-level ALTO and images require explicit ``views``. This prevents an
        accidental whole-document download from turning one call into thousands
        of requests. Completed files are individually reused when resuming.
        """
        normalized_views = self._normalize_views(views)
        if not metadata and not text and not alto and not images:
            raise ValueError("at least one artifact must be requested")
        if (alto or images) and not normalized_views:
            raise ValueError("views must be provided when requesting ALTO or images")
        if image_width < 1:
            raise ValueError("image_width must be >= 1")

        root = Path(output)
        manifest = root / "manifest.jsonl"
        results: list[CorpusItemResult] = []

        for ark in self.arks:
            document_dir = root / "documents" / ark
            metadata_file = document_dir / "metadata.json"
            text_file = document_dir / "text.txt"
            alto_files = tuple(document_dir / "pages" / str(view) / "alto.xml" for view in normalized_views)
            image_files = tuple(document_dir / "pages" / str(view) / "image.jpg" for view in normalized_views)

            requested_paths: list[Path] = []
            if metadata:
                requested_paths.append(metadata_file)
            if text:
                requested_paths.append(text_file)
            if alto:
                requested_paths.extend(alto_files)
            if images:
                requested_paths.extend(image_files)

            if resume and all(path.is_file() for path in requested_paths):
                results.append(
                    CorpusItemResult(
                        ark=ark,
                        status="skipped",
                        metadata_path=str(metadata_file) if metadata else None,
                        text_path=str(text_file) if text else None,
                        alto_paths=tuple(str(path) for path in alto_files) if alto else (),
                        image_paths=tuple(str(path) for path in image_files) if images else (),
                    )
                )
                continue

            try:
                doc = self._gallica.document(ark)
                if metadata and not (resume and metadata_file.is_file()):
                    self._write_atomic(metadata_file, self._metadata_json(doc.metadata()))
                if text and not (resume and text_file.is_file()):
                    self._write_atomic(text_file, doc.text())
                if alto:
                    for view, path in zip(normalized_views, alto_files, strict=True):
                        if not (resume and path.is_file()):
                            self._write_atomic_bytes(path, doc.page(view).alto())
                if images:
                    for view, path in zip(normalized_views, image_files, strict=True):
                        if not (resume and path.is_file()):
                            self._write_atomic_bytes(
                                path,
                                doc.page(view).image(width=image_width, fmt="jpg"),
                            )
                item = CorpusItemResult(
                    ark=ark,
                    status="success",
                    metadata_path=str(metadata_file) if metadata else None,
                    text_path=str(text_file) if text else None,
                    alto_paths=tuple(str(path) for path in alto_files) if alto else (),
                    image_paths=tuple(str(path) for path in image_files) if images else (),
                )
            except Exception as exc:  # noqa: BLE001 - per-item failure isolation is the contract
                item = CorpusItemResult(
                    ark=ark,
                    status="error",
                    metadata_path=str(metadata_file) if metadata and metadata_file.is_file() else None,
                    text_path=str(text_file) if text and text_file.is_file() else None,
                    alto_paths=tuple(str(path) for path in alto_files if path.is_file()) if alto else (),
                    image_paths=tuple(str(path) for path in image_files if path.is_file()) if images else (),
                    error=f"{type(exc).__name__}: {exc}",
                )
            self._append_manifest(manifest, item)
            results.append(item)

        return CorpusReport(items=tuple(results), manifest_path=str(manifest))

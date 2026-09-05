from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

import httpx

from ._version import __version__
from .ark import normalize_ark

if TYPE_CHECKING:
    from .client import Gallica

CorpusStatus = Literal["success", "error", "skipped"]
ArtifactKind = Literal["metadata", "text", "alto", "image"]
_ARTIFACT_CONTRACT_VERSION = 1
_MANIFEST_VERSION = 2
_RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


@dataclass(frozen=True, slots=True)
class CorpusArtifactRecord:
    kind: ArtifactKind
    path: str
    fingerprint: str
    sha256: str
    size: int
    parameters: dict[str, object]
    sdk_version: str


@dataclass(frozen=True, slots=True)
class CorpusArtifactFailure:
    """Structured failure for one requested corpus artifact."""

    kind: ArtifactKind
    path: str
    fingerprint: str
    parameters: dict[str, object]
    error_type: str
    message: str
    retryable: bool
    sdk_version: str


@dataclass(frozen=True, slots=True)
class CorpusItemResult:
    ark: str
    status: CorpusStatus
    metadata_path: str | None = None
    text_path: str | None = None
    alto_paths: tuple[str, ...] = ()
    image_paths: tuple[str, ...] = ()
    artifacts: tuple[CorpusArtifactRecord, ...] = ()
    failure_details: tuple[CorpusArtifactFailure, ...] = ()
    error: str | None = None

    @property
    def retryable(self) -> bool:
        """Whether at least one failed artifact may succeed on a later retry."""
        return any(failure.retryable for failure in self.failure_details)


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

    @property
    def retryable(self) -> tuple[CorpusItemResult, ...]:
        """Failed items containing at least one retryable artifact failure."""
        return tuple(item for item in self.failures if item.retryable)


@dataclass(frozen=True, slots=True)
class _ArtifactRequest:
    kind: ArtifactKind
    path: Path
    relative_path: str
    fingerprint: str
    parameters: dict[str, object]


class Corpus:
    """A small, resumable collection of Gallica documents.

    Corpus stays synchronous and delegates every network operation to normal SDK
    primitives so central throttling and retry policies remain authoritative.
    Failures are isolated per requested artifact so one bad response does not hide
    independent artifacts that can still be retrieved for the same ARK.
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
        payload = asdict(item)
        payload["_manifest_version"] = _MANIFEST_VERSION
        payload["_sdk_version"] = __version__
        payload["_written_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
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

    @staticmethod
    def _fingerprint(*, ark: str, kind: ArtifactKind, parameters: dict[str, object]) -> str:
        payload = {
            "contract_version": _ARTIFACT_CONTRACT_VERSION,
            "ark": ark,
            "kind": kind,
            "parameters": parameters,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @classmethod
    def _request(
        cls,
        root: Path,
        path: Path,
        *,
        ark: str,
        kind: ArtifactKind,
        parameters: dict[str, object] | None = None,
    ) -> _ArtifactRequest:
        normalized_parameters = dict(parameters or {})
        return _ArtifactRequest(
            kind=kind,
            path=path,
            relative_path=path.relative_to(root).as_posix(),
            fingerprint=cls._fingerprint(
                ark=ark,
                kind=kind,
                parameters=normalized_parameters,
            ),
            parameters=normalized_parameters,
        )

    @staticmethod
    def _record_for(request: _ArtifactRequest) -> CorpusArtifactRecord:
        content = request.path.read_bytes()
        return CorpusArtifactRecord(
            kind=request.kind,
            path=request.relative_path,
            fingerprint=request.fingerprint,
            sha256=hashlib.sha256(content).hexdigest(),
            size=len(content),
            parameters=request.parameters,
            sdk_version=__version__,
        )

    @staticmethod
    def _load_manifest_artifacts(path: Path) -> dict[str, CorpusArtifactRecord]:
        if not path.is_file():
            return {}
        known: dict[str, CorpusArtifactRecord] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            artifacts = payload.get("artifacts")
            if not isinstance(artifacts, list):
                continue
            for raw in artifacts:
                if not isinstance(raw, dict):
                    continue
                try:
                    record = CorpusArtifactRecord(
                        kind=raw["kind"],
                        path=str(raw["path"]),
                        fingerprint=str(raw["fingerprint"]),
                        sha256=str(raw["sha256"]),
                        size=int(raw["size"]),
                        parameters=dict(raw["parameters"]),
                        sdk_version=str(raw["sdk_version"]),
                    )
                except (KeyError, TypeError, ValueError):
                    continue
                known[record.path] = record
        return known

    @staticmethod
    def _is_reusable(
        root: Path,
        request: _ArtifactRequest,
        known: dict[str, CorpusArtifactRecord],
    ) -> CorpusArtifactRecord | None:
        record = known.get(request.relative_path)
        if record is None or record.fingerprint != request.fingerprint:
            return None
        path = root / record.path
        if not path.is_file():
            return None
        content = path.read_bytes()
        if len(content) != record.size:
            return None
        if hashlib.sha256(content).hexdigest() != record.sha256:
            return None
        return record

    @staticmethod
    def _paths_for_kind(
        requests: tuple[_ArtifactRequest, ...],
        records: dict[str, CorpusArtifactRecord],
        kind: ArtifactKind,
    ) -> tuple[str, ...]:
        return tuple(
            str(request.path)
            for request in requests
            if request.kind == kind and request.relative_path in records
        )

    @staticmethod
    def _failure_for(request: _ArtifactRequest, exc: Exception) -> CorpusArtifactFailure:
        retryable = isinstance(exc, httpx.TransportError)
        if isinstance(exc, httpx.HTTPStatusError):
            retryable = exc.response.status_code in _RETRYABLE_HTTP_STATUSES
        return CorpusArtifactFailure(
            kind=request.kind,
            path=request.relative_path,
            fingerprint=request.fingerprint,
            parameters=request.parameters,
            error_type=type(exc).__name__,
            message=str(exc),
            retryable=retryable,
            sdk_version=__version__,
        )

    @staticmethod
    def _error_summary(failures: list[CorpusArtifactFailure]) -> str | None:
        if not failures:
            return None
        return "; ".join(
            f"{failure.kind}: {failure.error_type}: {failure.message}" for failure in failures
        )

    def _fetch_artifact(self, request: _ArtifactRequest, doc: object) -> None:
        from .document import Document

        if not isinstance(doc, Document):
            typed_doc = cast("Document", doc)
        else:
            typed_doc = doc
        if request.kind == "metadata":
            self._write_atomic(request.path, self._metadata_json(typed_doc.metadata()))
        elif request.kind == "text":
            self._write_atomic(request.path, typed_doc.text())
        elif request.kind == "alto":
            view = int(cast(int | str, request.parameters["view"]))
            self._write_atomic_bytes(request.path, typed_doc.page(view).alto())
        else:
            view = int(cast(int | str, request.parameters["view"]))
            width = int(cast(int | str, request.parameters["width"]))
            self._write_atomic_bytes(
                request.path,
                typed_doc.page(view).image(width=width, fmt="jpg"),
            )

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

        Page-level ALTO and images require explicit ``views``. Resume only reuses
        artifacts whose request fingerprint, byte size and SHA-256 checksum match
        provenance recorded in ``manifest.jsonl``. Individual artifact failures do
        not prevent independent requested artifacts for the same ARK from running.
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
        known_artifacts = self._load_manifest_artifacts(manifest) if resume else {}
        results: list[CorpusItemResult] = []

        for ark in self.arks:
            document_dir = root / "documents" / ark
            requests_list: list[_ArtifactRequest] = []
            if metadata:
                requests_list.append(
                    self._request(
                        root,
                        document_dir / "metadata.json",
                        ark=ark,
                        kind="metadata",
                    )
                )
            if text:
                requests_list.append(
                    self._request(root, document_dir / "text.txt", ark=ark, kind="text")
                )
            if alto:
                for view in normalized_views:
                    requests_list.append(
                        self._request(
                            root,
                            document_dir / "pages" / str(view) / "alto.xml",
                            ark=ark,
                            kind="alto",
                            parameters={"view": view},
                        )
                    )
            if images:
                for view in normalized_views:
                    requests_list.append(
                        self._request(
                            root,
                            document_dir / "pages" / str(view) / "image.jpg",
                            ark=ark,
                            kind="image",
                            parameters={"view": view, "width": image_width, "format": "jpg"},
                        )
                    )
            requests = tuple(requests_list)

            current: dict[str, CorpusArtifactRecord] = {}
            if resume:
                for request in requests:
                    record = self._is_reusable(root, request, known_artifacts)
                    if record is not None:
                        current[request.relative_path] = record

            metadata_request = next((item for item in requests if item.kind == "metadata"), None)
            text_request = next((item for item in requests if item.kind == "text"), None)

            if len(current) == len(requests):
                results.append(
                    CorpusItemResult(
                        ark=ark,
                        status="skipped",
                        metadata_path=str(metadata_request.path) if metadata_request else None,
                        text_path=str(text_request.path) if text_request else None,
                        alto_paths=self._paths_for_kind(requests, current, "alto"),
                        image_paths=self._paths_for_kind(requests, current, "image"),
                        artifacts=tuple(current[item.relative_path] for item in requests),
                    )
                )
                continue

            doc = self._gallica.document(ark)
            failure_details: list[CorpusArtifactFailure] = []
            for request in requests:
                if request.relative_path in current:
                    continue
                try:
                    self._fetch_artifact(request, doc)
                    current[request.relative_path] = self._record_for(request)
                except Exception as exc:  # noqa: BLE001 - per-artifact isolation is the contract
                    failure_details.append(self._failure_for(request, exc))

            item = CorpusItemResult(
                ark=ark,
                status="error" if failure_details else "success",
                metadata_path=(
                    str(metadata_request.path)
                    if metadata_request and metadata_request.relative_path in current
                    else None
                ),
                text_path=(
                    str(text_request.path)
                    if text_request and text_request.relative_path in current
                    else None
                ),
                alto_paths=self._paths_for_kind(requests, current, "alto"),
                image_paths=self._paths_for_kind(requests, current, "image"),
                artifacts=tuple(
                    current[request.relative_path]
                    for request in requests
                    if request.relative_path in current
                ),
                failure_details=tuple(failure_details),
                error=self._error_summary(failure_details),
            )
            self._append_manifest(manifest, item)
            for record in item.artifacts:
                known_artifacts[record.path] = record
            results.append(item)

        return CorpusReport(items=tuple(results), manifest_path=str(manifest))

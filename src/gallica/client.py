from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from datetime import date, timedelta
from typing import Self, cast
from urllib.parse import quote

import httpx

from .agent import CapabilitySpec
from .agent import capabilities as capability_contracts
from .ark import ark_uri, normalize_ark
from .corpus import Corpus
from .document import Document
from .exceptions import GallicaResponseError
from .models import (
    ContentSearchResults,
    DocumentMetadata,
    DublinCoreRecord,
    Pagination,
    SearchResults,
    TocDocument,
)
from .parsing import parse_content_search, parse_oai_record, parse_pagination, parse_sru
from .periodical import Periodical
from .transport import Transport

BASE_URL = "https://gallica.bnf.fr"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _looks_like_html(content: bytes) -> bool:
    prefix = content.lstrip()[:64].lower()
    return prefix.startswith((b"<!doctype html", b"<html"))


def _reject_html(response: httpx.Response, *, service: str) -> None:
    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" in content_type or _looks_like_html(response.content):
        raise GallicaResponseError(f"{service} returned HTML instead of the expected payload")


def _validate_alto(response: httpx.Response) -> bytes:
    _reject_html(response, service="ALTO")
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise GallicaResponseError("ALTO response is not valid XML") from exc
    if _local_name(root.tag).lower() != "alto":
        raise GallicaResponseError(
            f"ALTO response has unexpected root {_local_name(root.tag)!r}"
        )
    return response.content


def _validate_image(response: httpx.Response) -> bytes:
    content = response.content
    if not content:
        raise GallicaResponseError("IIIF image response is empty")
    _reject_html(response, service="IIIF image")
    content_type = response.headers.get("Content-Type", "").lower()
    if content_type.startswith("image/"):
        return content
    signatures = (
        b"\xff\xd8\xff",
        b"\x89PNG\r\n\x1a\n",
        b"GIF87a",
        b"GIF89a",
        b"RIFF",
        b"\x00\x00\x00\x0cjP  \r\n\x87\n",
    )
    if any(content.startswith(signature) for signature in signatures):
        return content
    raise GallicaResponseError(
        f"IIIF image response has unexpected content type {content_type or '<missing>'!r}"
    )


def _validate_text(response: httpx.Response) -> str:
    if not response.content.strip():
        raise GallicaResponseError("plain OCR text response is empty")
    final_path = response.url.path.lower()
    prefix = response.content[:16384].lower()
    if "/altcha" in final_path or b"altcha-widget" in prefix or b"/search/altcha" in prefix:
        raise GallicaResponseError("plain OCR text request was redirected to an anti-bot challenge")
    return response.text


def _validate_toc(response: httpx.Response) -> TocDocument:
    if not response.content.strip():
        raise GallicaResponseError("Toc response is empty")
    if _looks_like_html(response.content):
        return TocDocument(format="html", raw=response.text)
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise GallicaResponseError("Toc response is neither valid HTML nor XML") from exc
    if _local_name(root.tag) not in {"TEI.2", "TEI"}:
        raise GallicaResponseError(
            f"Toc response has unexpected XML root {_local_name(root.tag)!r}"
        )
    return TocDocument(format="tei", raw=response.text)


class Gallica:
    """Entry point for the public Gallica APIs."""

    def __init__(self, transport: Transport | None = None) -> None:
        self._transport = transport or Transport()

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    @staticmethod
    def capabilities() -> tuple[CapabilitySpec, ...]:
        return capability_contracts()

    def document(self, ark: str) -> Document:
        return Document(self, normalize_ark(ark))

    def periodical(self, ark: str) -> Periodical:
        return Periodical(self, normalize_ark(ark))

    def corpus(self, arks: Iterable[str]) -> Corpus:
        return Corpus(self, arks)

    def search(
        self,
        query: str,
        *,
        start_record: int = 1,
        maximum_records: int = 50,
    ) -> SearchResults:
        if start_record < 1:
            raise ValueError("start_record must be >= 1")
        if not 1 <= maximum_records <= 50:
            raise ValueError("maximum_records must be between 1 and 50")
        response = self._transport.get(
            f"{BASE_URL}/SRU",
            params={
                "operation": "searchRetrieve",
                "version": "1.2",
                "query": query,
                "startRecord": str(start_record),
                "maximumRecords": str(maximum_records),
            },
        )
        return parse_sru(response.text, fallback_query=query)

    def search_all(
        self,
        query: str,
        *,
        limit: int | None = None,
        page_size: int = 50,
    ) -> Iterator[DublinCoreRecord]:
        if limit is not None and limit < 1:
            raise ValueError("limit must be >= 1 when supplied")
        if not 1 <= page_size <= 50:
            raise ValueError("page_size must be between 1 and 50")
        yielded = 0
        start_record = 1
        while True:
            requested = page_size if limit is None else min(page_size, limit - yielded)
            if requested <= 0:
                return
            page = self.search(query, start_record=start_record, maximum_records=requested)
            if not page.records:
                return
            for record in page.records:
                yield record
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            start_record += len(page.records)
            if start_record > page.total:
                return

    def _metadata(self, ark: str) -> DocumentMetadata:
        normalized = normalize_ark(ark)
        response = self._transport.get(
            f"{BASE_URL}/services/OAIRecord", params={"ark": normalized}
        )
        return parse_oai_record(response.text, ark=normalized)

    def _pagination(self, ark: str) -> Pagination:
        response = self._transport.get(
            f"{BASE_URL}/services/Pagination", params={"ark": normalize_ark(ark)}
        )
        if _looks_like_html(response.content):
            raise GallicaResponseError("Pagination returned HTML instead of XML")
        return parse_pagination(response.text)

    def _page_count(self, ark: str) -> int:
        return self._pagination(ark).image_views

    def _toc(self, ark: str) -> TocDocument:
        response = self._transport.get(
            f"{BASE_URL}/services/Toc",
            params={"ark": f"ark:/12148/{normalize_ark(ark)}"},
        )
        return _validate_toc(response)

    def _text(self, ark: str, *, start_view: int | None = None, nviews: int | None = None) -> str:
        root = f"{BASE_URL}/ark:/12148/{normalize_ark(ark)}"
        if start_view is None:
            url = f"{root}.texteBrut"
        else:
            if start_view < 1:
                raise ValueError("start_view must be >= 1")
            if nviews is None or nviews < 1:
                raise ValueError("nviews must be >= 1 when start_view is provided")
            url = f"{root}/f{start_view}n{nviews}.texteBrut"
        return _validate_text(self._transport.get(url, bucket="text"))

    def _content_search(
        self,
        ark: str,
        query: str,
        *,
        page: int | None = None,
        start_result: int | None = None,
    ) -> ContentSearchResults:
        params = {"ark": normalize_ark(ark), "query": query}
        if page is not None:
            if page < 1:
                raise ValueError("page must be >= 1")
            params["page"] = str(page)
        if start_result is not None:
            if start_result < 1:
                raise ValueError("start_result must be >= 1")
            params["startResult"] = str(start_result)
        response = self._transport.get(f"{BASE_URL}/services/ContentSearch", params=params)
        return parse_content_search(response.text, fallback_query=query)

    def _alto(self, ark: str, view: int) -> bytes:
        if view < 1:
            raise ValueError("view must be >= 1")
        response = self._transport.get(
            f"{BASE_URL}/RequestDigitalElement",
            params={"O": normalize_ark(ark), "E": "ALTO", "Deb": str(view)},
        )
        return _validate_alto(response)

    def _issue_for_date(self, ark: str, when: date) -> str | None:
        response = self._transport.get(
            f"{BASE_URL}/services/Issues",
            params={"ark": f"ark:/12148/{normalize_ark(ark)}/date", "date": str(when.year)},
        )
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            raise GallicaResponseError("Issues response is not valid XML") from exc
        if _local_name(root.tag) not in {"issues", "results"}:
            raise GallicaResponseError(
                f"Issues response has unexpected root {_local_name(root.tag)!r}"
            )
        for element in root.iter():
            if _local_name(element.tag) != "issue":
                continue
            issue_ark = element.attrib.get("ark")
            raw_day = element.attrib.get("dayOfYear")
            if not issue_ark or not raw_day:
                continue
            try:
                issue_date = date(when.year, 1, 1) + timedelta(days=int(raw_day) - 1)
            except (ValueError, OverflowError):
                continue
            if issue_date == when:
                return normalize_ark(issue_ark)
        return None

    def _iiif_info(self, ark: str, view: int) -> dict[str, object]:
        if view < 1:
            raise ValueError("view must be >= 1")
        response = self._transport.get(f"{BASE_URL}/iiif/{ark_uri(ark)}/f{view}/info.json")
        _reject_html(response, service="IIIF info.json")
        try:
            payload: object = response.json()
        except ValueError as exc:
            raise GallicaResponseError("IIIF info response is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise GallicaResponseError("IIIF info response is not a JSON object")
        width = payload.get("width")
        height = payload.get("height")
        if not isinstance(width, int) or width < 1 or not isinstance(height, int) or height < 1:
            raise GallicaResponseError("IIIF info response lacks positive integer width/height")
        return cast(dict[str, object], payload)

    @staticmethod
    def _iiif_bucket(size: str) -> str:
        if size == "full":
            return "iiif_hd"
        token = size.split(",", 1)[0].lstrip("!^")
        try:
            return "iiif_hd" if int(token) > 1000 else "default"
        except ValueError:
            return "default"

    def _image(
        self,
        ark: str,
        view: int,
        *,
        width: int = 1000,
        fmt: str = "jpg",
    ) -> bytes:
        if view < 1:
            raise ValueError("view must be >= 1")
        if width < 1:
            raise ValueError("width must be >= 1")
        if not re.fullmatch(r"[A-Za-z0-9]+", fmt):
            raise ValueError("invalid IIIF image format")
        size = f"{width},"
        url = (
            f"{BASE_URL}/iiif/{ark_uri(ark)}/f{view}/full/"
            f"{quote(size, safe=',!^')}/0/native.{fmt}"
        )
        response = self._transport.get(url, bucket=self._iiif_bucket(size))
        return _validate_image(response)

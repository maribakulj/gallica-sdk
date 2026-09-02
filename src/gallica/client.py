from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Self, cast
from urllib.parse import quote

from .ark import ark_uri, normalize_ark
from .document import Document
from .periodical import Periodical
from .transport import Transport

BASE_URL = "https://gallica.bnf.fr"


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

    def document(self, ark: str) -> Document:
        return Document(self, normalize_ark(ark))

    def periodical(self, ark: str) -> Periodical:
        return Periodical(self, normalize_ark(ark))

    def search(
        self,
        query: str,
        *,
        start_record: int = 1,
        maximum_records: int = 50,
    ) -> str:
        """Run a raw SRU 1.2 search and return the XML response as text."""
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
        return response.text

    def _metadata(self, ark: str) -> str:
        response = self._transport.get(
            f"{BASE_URL}/services/OAIRecord", params={"ark": normalize_ark(ark)}
        )
        return response.text

    def _page_count(self, ark: str) -> int:
        response = self._transport.get(
            f"{BASE_URL}/services/Pagination", params={"ark": normalize_ark(ark)}
        )
        root = ET.fromstring(response.content)
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] == "nbVueImages" and element.text:
                count = int(element.text)
                if count > 0:
                    return count
        raise ValueError("Pagination response does not contain a valid nbVueImages")

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
        return self._transport.get(url, bucket="text").text

    def _content_search(
        self,
        ark: str,
        query: str,
        *,
        page: int | None = None,
        start_result: int | None = None,
    ) -> str:
        params = {"ark": normalize_ark(ark), "query": query}
        if page is not None:
            if page < 1:
                raise ValueError("page must be >= 1")
            params["page"] = str(page)
        if start_result is not None:
            if start_result < 1:
                raise ValueError("start_result must be >= 1")
            params["startResult"] = str(start_result)
        return self._transport.get(f"{BASE_URL}/services/ContentSearch", params=params).text

    def _alto(self, ark: str, view: int) -> bytes:
        if view < 1:
            raise ValueError("view must be >= 1")
        response = self._transport.get(
            f"{BASE_URL}/RequestDigitalElement",
            params={"O": normalize_ark(ark), "E": "ALTO", "Deb": str(view)},
        )
        return response.content

    def _issue_for_date(self, ark: str, when: date) -> str | None:
        response = self._transport.get(
            f"{BASE_URL}/services/Issues",
            params={"ark": f"ark:/12148/{normalize_ark(ark)}/date", "date": str(when.year)},
        )
        root = ET.fromstring(response.content)
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "issue":
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
        payload: object = response.json()
        if not isinstance(payload, dict):
            raise TypeError("IIIF info response is not a JSON object")
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
        return self._transport.get(url, bucket=self._iiif_bucket(size)).content

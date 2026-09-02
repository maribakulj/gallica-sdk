from __future__ import annotations

import re
from urllib.parse import quote

from .ark import ark_uri, normalize_ark
from .transport import Transport

BASE_URL = "https://gallica.bnf.fr"


class Gallica:
    """Entry point for the public Gallica APIs."""

    def __init__(self, transport: Transport | None = None) -> None:
        self._transport = transport or Transport()

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Gallica:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def document(self, ark: str) -> "Document":
        from .document import Document

        return Document(self, normalize_ark(ark))

    def search(
        self,
        query: str,
        *,
        start_record: int = 1,
        maximum_records: int = 50,
    ) -> str:
        """Run a raw SRU 1.2 search and return the XML response as text.

        Structured result models are intentionally deferred until the real SRU
        shapes have been mapped more completely.
        """
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
        import xml.etree.ElementTree as ET

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

    def _alto(self, ark: str, view: int) -> bytes:
        if view < 1:
            raise ValueError("view must be >= 1")
        response = self._transport.get(
            f"{BASE_URL}/RequestDigitalElement",
            params={"O": normalize_ark(ark), "E": "ALTO", "Deb": str(view)},
        )
        return response.content

    def _iiif_info(self, ark: str, view: int) -> dict[str, object]:
        if view < 1:
            raise ValueError("view must be >= 1")
        response = self._transport.get(
            f"{BASE_URL}/iiif/{ark_uri(ark)}/f{view}/info.json"
        )
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("IIIF info response is not a JSON object")
        return payload

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

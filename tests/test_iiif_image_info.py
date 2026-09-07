from __future__ import annotations

import json

import httpx
import pytest

from gallica import Gallica, GallicaResponseError


class StaticTransport:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.last_url: str | None = None

    def close(self) -> None:
        pass

    def get(self, url: str, *, params=None, bucket: str = "default") -> httpx.Response:
        self.last_url = url
        return self.response


def _response(payload: object) -> httpx.Response:
    content = json.dumps(payload).encode()
    return httpx.Response(
        200,
        content=content,
        headers={"Content-Type": "application/json"},
        request=httpx.Request("GET", "https://gallica.bnf.fr/test"),
    )


def test_iiif_image_info_detects_v2_and_preserves_raw_json() -> None:
    payload = {
        "@context": "http://iiif.io/api/image/2/context.json",
        "@id": "https://gallica.bnf.fr/iiif/ark:/12148/bpt6k1/f1",
        "protocol": "http://iiif.io/api/image",
        "width": 1200,
        "height": 1800,
        "profile": [
            "http://iiif.io/api/image/2/level2.json",
            {"formats": ["jpg", "png"]},
        ],
    }
    response = _response(payload)
    transport = StaticTransport(response)
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    info = gallica.document("bpt6k1").page(1).iiif_info()

    assert info.version == "2"
    assert info.identifier == payload["@id"]
    assert info.context == ("http://iiif.io/api/image/2/context.json",)
    assert info.protocol == "http://iiif.io/api/image"
    assert info.profiles == ("http://iiif.io/api/image/2/level2.json",)
    assert info.width == 1200
    assert info.height == 1800
    assert info.raw_json == response.text
    assert transport.last_url == "https://gallica.bnf.fr/iiif/ark:/12148/bpt6k1/f1/info.json"


def test_iiif_image_info_detects_v3() -> None:
    payload = {
        "@context": "http://iiif.io/api/image/3/context.json",
        "id": "https://example.org/iiif/image/1",
        "protocol": "http://iiif.io/api/image",
        "width": 900,
        "height": 1400,
        "profile": "level2",
    }
    gallica = Gallica(transport=StaticTransport(_response(payload)))  # type: ignore[arg-type]

    info = gallica.document("bpt6k1").page(1).iiif_info()

    assert info.version == "3"
    assert info.identifier == payload["id"]
    assert info.profiles == ("level2",)


def test_iiif_image_info_rejects_conflicting_version_indicators() -> None:
    payload = {
        "@context": "http://iiif.io/api/image/2/context.json",
        "@id": "https://example.org/iiif/image/1",
        "width": 900,
        "height": 1400,
        "profile": "http://iiif.io/api/image/3/level2.json",
    }
    gallica = Gallica(transport=StaticTransport(_response(payload)))  # type: ignore[arg-type]

    with pytest.raises(GallicaResponseError, match="mixes v2 and v3"):
        gallica.document("bpt6k1").page(1).iiif_info()


def test_iiif_image_info_keeps_unknown_version_backward_compatible() -> None:
    payload = {"width": 900, "height": 1400}
    gallica = Gallica(transport=StaticTransport(_response(payload)))  # type: ignore[arg-type]

    info = gallica.document("bpt6k1").page(1).iiif_info()

    assert info.version == "unknown"
    assert info.identifier is None
    assert info.context == ()
    assert info.profiles == ()


def test_iiif_image_info_requires_version_specific_identifier() -> None:
    v2 = {
        "@context": "http://iiif.io/api/image/2/context.json",
        "width": 900,
        "height": 1400,
    }
    gallica = Gallica(transport=StaticTransport(_response(v2)))  # type: ignore[arg-type]

    with pytest.raises(GallicaResponseError, match="v2.*@id"):
        gallica.document("bpt6k1").page(1).iiif_info()

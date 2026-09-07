from __future__ import annotations

import json

import httpx
import pytest

from gallica import Gallica, GallicaResponseError, IIIFPresentationManifest


class StaticTransport:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.urls: list[str] = []

    def close(self) -> None:
        pass

    def get(self, url: str, *, params=None, bucket: str = "default") -> httpx.Response:
        self.urls.append(url)
        return self.response


def _json_response(payload: object) -> httpx.Response:
    return httpx.Response(
        200,
        content=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        request=httpx.Request("GET", "https://gallica.bnf.fr/iiif/test/manifest.json"),
    )


def test_document_iiif_manifest_parses_presentation_v2_without_normalizing() -> None:
    payload = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@id": "https://gallica.bnf.fr/iiif/ark:/12148/btv1b1/manifest.json",
        "@type": "sc:Manifest",
        "sequences": [
            {
                "@type": "sc:Sequence",
                "canvases": [
                    {"@id": "https://example.test/canvas/1", "@type": "sc:Canvas"},
                    {"@id": "https://example.test/canvas/2", "@type": "sc:Canvas"},
                ],
            }
        ],
    }
    transport = StaticTransport(_json_response(payload))
    gallica = Gallica(transport=transport)  # type: ignore[arg-type]

    manifest = gallica.document("btv1b1").iiif_manifest()

    assert isinstance(manifest, IIIFPresentationManifest)
    assert manifest.version == "2"
    assert manifest.identifier == payload["@id"]
    assert manifest.context == ("http://iiif.io/api/presentation/2/context.json",)
    assert manifest.canvas_count == 2
    assert json.loads(manifest.raw_json) == payload
    assert transport.urls == [
        "https://gallica.bnf.fr/iiif/ark:/12148/btv1b1/manifest.json"
    ]


def test_document_iiif_manifest_detects_presentation_v3() -> None:
    payload = {
        "@context": ["http://iiif.io/api/presentation/3/context.json"],
        "id": "https://example.test/manifest",
        "type": "Manifest",
        "items": [{"id": "https://example.test/canvas/1", "type": "Canvas"}],
    }
    gallica = Gallica(transport=StaticTransport(_json_response(payload)))  # type: ignore[arg-type]

    manifest = gallica.document("btv1b1").iiif_manifest()

    assert manifest.version == "3"
    assert manifest.identifier == "https://example.test/manifest"
    assert manifest.canvas_count == 1


def test_document_iiif_manifest_rejects_context_structure_conflict() -> None:
    payload = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "id": "https://example.test/manifest",
        "type": "Manifest",
        "items": [],
    }
    gallica = Gallica(transport=StaticTransport(_json_response(payload)))  # type: ignore[arg-type]

    with pytest.raises(GallicaResponseError, match="context conflicts"):
        gallica.document("btv1b1").iiif_manifest()


def test_document_iiif_manifest_rejects_mixed_version_structure() -> None:
    payload = {
        "@id": "https://example.test/manifest",
        "@type": "sc:Manifest",
        "sequences": [],
        "type": "Manifest",
        "items": [],
    }
    gallica = Gallica(transport=StaticTransport(_json_response(payload)))  # type: ignore[arg-type]

    with pytest.raises(GallicaResponseError, match="mixes v2 and v3 structure"):
        gallica.document("btv1b1").iiif_manifest()


def test_document_iiif_manifest_rejects_non_manifest_json() -> None:
    gallica = Gallica(transport=StaticTransport(_json_response({"hello": "world"})))  # type: ignore[arg-type]

    with pytest.raises(GallicaResponseError, match="not recognizable"):
        gallica.document("btv1b1").iiif_manifest()

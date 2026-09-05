from __future__ import annotations

import json
from pathlib import Path

from gallica.corpus import Corpus


class FailingPage:
    def image(self, *, width: int = 1000, fmt: str = "jpg") -> bytes:
        raise RuntimeError(f"image failed at width={width} fmt={fmt}")


class FailingDocument:
    def page(self, number: int) -> FailingPage:
        return FailingPage()


class FailingGallica:
    def document(self, ark: str) -> FailingDocument:
        return FailingDocument()


def test_manifest_records_version_and_failed_request_provenance(tmp_path: Path) -> None:
    corpus = Corpus(FailingGallica(), ["bpt6k1"])  # type: ignore[arg-type]

    report = corpus.fetch(
        tmp_path,
        metadata=False,
        images=True,
        views=[3],
        image_width=3000,
    )

    failure = report.failures[0].failure_details[0]
    assert failure.kind == "image"
    assert failure.parameters == {"view": 3, "width": 3000, "format": "jpg"}
    assert len(failure.fingerprint) == 64
    assert failure.sdk_version

    payload = json.loads((tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert payload["_manifest_version"] == 2
    assert payload["_sdk_version"] == failure.sdk_version
    assert payload["_written_at"].endswith("Z")
    manifest_failure = payload["failure_details"][0]
    assert manifest_failure["fingerprint"] == failure.fingerprint
    assert manifest_failure["parameters"]["width"] == 3000
    assert manifest_failure["parameters"]["view"] == 3

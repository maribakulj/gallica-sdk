from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

from .agent import capabilities
from .client import Gallica
from .models import Categories, IIIFImageInfo, IIIFPresentationManifest, Pagination, TocDocument
from .operational import operational_contract
from .reference import programmable_reference


def _bounded_records(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 50:
        raise argparse.ArgumentTypeError("limit must be between 1 and 50")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def _dump(payload: object, *, pretty: bool) -> None:
    if pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def _metadata_payload(metadata: Any) -> dict[str, object]:
    return {
        "ark": metadata.ark,
        "indexing_mode": metadata.indexing_mode,
        "ocr_quality": metadata.ocr_quality,
        "record": metadata.record.as_dict(),
    }


def _categories_payload(categories: Categories) -> dict[str, object]:
    return {
        "query": categories.query,
        "categories": list(categories.categories),
        "values": [
            {
                "category": item.category,
                "clean_value": item.clean_value,
                "label": item.label,
                "display_value": item.display_value,
                "approximate_count": item.approximate_count,
                "cql_field": item.cql_field,
            }
            for item in categories.values
        ],
    }


def _pagination_payload(ark: str, pagination: Pagination) -> dict[str, object]:
    return {
        "ark": ark,
        "first_displayed_page": pagination.first_displayed_page,
        "has_toc": pagination.has_toc,
        "toc_location": pagination.toc_location,
        "has_content": pagination.has_content,
        "digital_id": pagination.digital_id,
        "image_views": pagination.image_views,
        "audio_views": pagination.audio_views,
        "pages": [
            {
                "number": page.number,
                "order": page.order,
                "pagination_type": page.pagination_type,
                "legend": page.legend,
            }
            for page in pagination.pages
        ],
    }


def _toc_payload(ark: str, toc: TocDocument) -> dict[str, object]:
    return {
        "ark": ark,
        "format": toc.format,
        "well_formed": toc.well_formed,
        "raw": toc.raw,
    }


def _iiif_manifest_payload(ark: str, manifest: IIIFPresentationManifest) -> dict[str, object]:
    return {
        "ark": ark,
        "version": manifest.version,
        "identifier": manifest.identifier,
        "context": list(manifest.context),
        "canvas_count": manifest.canvas_count,
    }


def _iiif_info_payload(ark: str, view: int, info: IIIFImageInfo) -> dict[str, object]:
    return {
        "ark": ark,
        "view": view,
        "version": info.version,
        "identifier": info.identifier,
        "context": list(info.context),
        "protocol": info.protocol,
        "profiles": list(info.profiles),
        "width": info.width,
        "height": info.height,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gallica", description="Typed access to public Gallica services.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("reference", help="Print the programmable Gallica reference.")
    subparsers.add_parser("capabilities", help="Print the compact capability contracts.")

    contract = subparsers.add_parser("contract", help="Print one resolved operational contract.")
    contract.add_argument("capability_id")

    search = subparsers.add_parser("search", help="Run one SRU search page.")
    search.add_argument("query")
    search.add_argument("--limit", type=_bounded_records, default=10)
    search.add_argument("--start-record", type=int, default=1)

    categories = subparsers.add_parser("categories", help="Fetch typed Categories refinements.")
    categories.add_argument("query")

    metadata = subparsers.add_parser("metadata", help="Fetch typed metadata for one ARK.")
    metadata.add_argument("ark")

    page_count = subparsers.add_parser("page-count", help="Fetch the number of image views for one ARK.")
    page_count.add_argument("ark")

    pagination = subparsers.add_parser("pagination", help="Fetch the complete typed Pagination structure.")
    pagination.add_argument("ark")

    toc = subparsers.add_parser("toc", help="Fetch the table of contents while preserving HTML/TEI form.")
    toc.add_argument("ark")

    manifest = subparsers.add_parser("iiif-manifest", help="Fetch typed IIIF Presentation metadata.")
    manifest.add_argument("ark")

    info = subparsers.add_parser("iiif-info", help="Fetch typed IIIF Image info.json metadata.")
    info.add_argument("ark")
    info.add_argument("view", type=_positive_int)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pretty = bool(args.pretty)

    if args.command == "reference":
        _dump(programmable_reference(), pretty=pretty)
        return 0
    if args.command == "capabilities":
        _dump(capabilities(), pretty=pretty)
        return 0
    if args.command == "contract":
        try:
            contract = operational_contract(args.capability_id)
        except KeyError as exc:
            build_parser().error(str(exc))
        _dump(contract, pretty=pretty)
        return 0

    with Gallica() as gallica:
        if args.command == "search":
            if args.start_record < 1:
                build_parser().error("--start-record must be >= 1")
            results = gallica.search(
                args.query,
                start_record=args.start_record,
                maximum_records=args.limit,
            )
            _dump(
                {
                    "query": results.query,
                    "total": results.total,
                    "records": [record.as_dict() for record in results.records],
                },
                pretty=pretty,
            )
            return 0
        if args.command == "categories":
            _dump(_categories_payload(gallica.categories(args.query)), pretty=pretty)
            return 0
        if args.command == "metadata":
            metadata = gallica.document(args.ark).metadata()
            _dump(_metadata_payload(metadata), pretty=pretty)
            return 0
        if args.command == "page-count":
            document = gallica.document(args.ark)
            _dump({"ark": document.ark, "page_count": document.page_count()}, pretty=pretty)
            return 0
        if args.command == "pagination":
            document = gallica.document(args.ark)
            _dump(_pagination_payload(document.ark, document.pagination()), pretty=pretty)
            return 0
        if args.command == "toc":
            document = gallica.document(args.ark)
            _dump(_toc_payload(document.ark, document.toc()), pretty=pretty)
            return 0
        if args.command == "iiif-manifest":
            document = gallica.document(args.ark)
            _dump(_iiif_manifest_payload(document.ark, document.iiif_manifest()), pretty=pretty)
            return 0
        if args.command == "iiif-info":
            document = gallica.document(args.ark)
            _dump(
                _iiif_info_payload(document.ark, args.view, document.page(args.view).iiif_info()),
                pretty=pretty,
            )
            return 0

    raise RuntimeError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

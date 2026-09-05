from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

from .agent import capabilities
from .client import Gallica
from .operational import operational_contract
from .reference import programmable_reference


def _bounded_records(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 50:
        raise argparse.ArgumentTypeError("limit must be between 1 and 50")
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

    metadata = subparsers.add_parser("metadata", help="Fetch typed metadata for one ARK.")
    metadata.add_argument("ark")

    page_count = subparsers.add_parser("page-count", help="Fetch the number of image views for one ARK.")
    page_count.add_argument("ark")

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
        if args.command == "metadata":
            metadata = gallica.document(args.ark).metadata()
            _dump(_metadata_payload(metadata), pretty=pretty)
            return 0
        if args.command == "page-count":
            document = gallica.document(args.ark)
            _dump({"ark": document.ark, "page_count": document.page_count()}, pretty=pretty)
            return 0

    raise RuntimeError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

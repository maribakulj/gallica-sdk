from __future__ import annotations

import argparse
from pathlib import Path

from gallica import capabilities, capability_evidence, programmable_reference

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- BEGIN GENERATED: canonical-capabilities -->"
END = "<!-- END GENERATED: canonical-capabilities -->"


def _format_default(value: object) -> str:
    if isinstance(value, str):
        return repr(value)
    return str(value)


def _signature(spec: dict[str, object]) -> str:
    parameters = spec["parameters"]
    assert isinstance(parameters, tuple)
    rendered: list[str] = []
    for raw in parameters:
        assert isinstance(raw, dict)
        name = str(raw["name"])
        if raw.get("required", False):
            rendered.append(name)
        else:
            rendered.append(f"{name}={_format_default(raw.get('default'))}")
    return f"{spec['call']}({', '.join(rendered)}) -> {spec['returns']}"


def _status_by_capability() -> dict[str, str]:
    reference = programmable_reference()
    services = {item["id"]: item for item in reference["services"]}
    links = {item["capability"]: item for item in capability_evidence()}
    result: dict[str, str] = {}
    for spec in capabilities():
        capability_id = spec["id"]
        service_ids = links[capability_id]["services"]
        if not service_ids:
            result[capability_id] = "local"
            continue
        statuses = {services[service_id]["status"] for service_id in service_ids}
        if len(statuses) == 1:
            result[capability_id] = next(iter(statuses))
        else:
            result[capability_id] = "mixed: " + ", ".join(sorted(statuses))
    return result


def _escape_table(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _readme_block() -> str:
    lines = [BEGIN, "```text"]
    lines.extend(_signature(dict(spec)) for spec in capabilities())
    lines.extend(["```", END])
    return "\n".join(lines)


def _capabilities_table_block() -> str:
    statuses = _status_by_capability()
    lines = [
        BEGIN,
        "| ID | Appel Python | Service | Retour | Statut | Contraintes canoniques |",
        "|---|---|---|---|---|---|",
    ]
    for spec in capabilities():
        constraints = "<br>".join(_escape_table(item) for item in spec["constraints"])
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape_table(spec['id'])}`",
                    f"`{_escape_table(_signature(dict(spec)))}`",
                    _escape_table(spec["network_service"]),
                    f"`{_escape_table(spec['returns'])}`",
                    _escape_table(statuses[spec["id"]]),
                    constraints,
                )
            )
            + " |"
        )
    lines.append(END)
    return "\n".join(lines)


def _replace_generated(text: str, block: str, *, path: Path) -> str:
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError(f"{path} must contain exactly one generated capability block")
    start = text.index(BEGIN)
    end = text.index(END, start) + len(END)
    return text[:start] + block + text[end:]


def update_documents(*, check: bool) -> tuple[Path, ...]:
    targets = {
        ROOT / "README.md": _readme_block(),
        ROOT / "docs" / "capabilities.md": _capabilities_table_block(),
    }
    stale: list[Path] = []
    for path, block in targets.items():
        current = path.read_text(encoding="utf-8")
        expected = _replace_generated(current, block, path=path)
        if current == expected:
            continue
        if check:
            stale.append(path.relative_to(ROOT))
        else:
            path.write_text(expected, encoding="utf-8")
    return tuple(stale)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate canonical capability sections in human documentation."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail instead of rewriting files when generated sections are stale.",
    )
    args = parser.parse_args()
    stale = update_documents(check=args.check)
    if stale:
        rendered = ", ".join(str(path) for path in stale)
        raise SystemExit(
            f"generated documentation is stale: {rendered}; run python scripts/generate_docs.py"
        )


if __name__ == "__main__":
    main()

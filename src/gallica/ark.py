from __future__ import annotations

import re

_ARK_RE = re.compile(r"^(?:https?://gallica\.bnf\.fr/)?(?:ark:/12148/)?(?P<id>[A-Za-z0-9]+)(?:/.*)?$")


def normalize_ark(value: str) -> str:
    """Return the Gallica identifier portion of an ARK.

    Accepted examples include ``bpt6k5738219s``, ``ark:/12148/bpt6k5738219s``
    and canonical Gallica URLs.
    """
    candidate = value.strip()
    match = _ARK_RE.fullmatch(candidate)
    if match is None:
        raise ValueError(f"Invalid Gallica ARK: {value!r}")
    return match.group("id")


def ark_uri(value: str) -> str:
    """Return a canonical ``ark:/12148/...`` URI."""
    return f"ark:/12148/{normalize_ark(value)}"

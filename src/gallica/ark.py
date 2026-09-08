from __future__ import annotations

import re

_GALLICA_HOST = r"https?://gallica\.bnf\.fr/"
_ARK_PREFIX = r"ark:/12148/"
# A Gallica host prefix is only accepted together with an explicit ark:/12148/
# marker: without it, a URL such as .../services/OAIRecord?ark=... would silently
# normalize to its first path segment instead of failing.
_ARK_RE = re.compile(
    rf"^(?:{_GALLICA_HOST}{_ARK_PREFIX}|{_ARK_PREFIX}|)(?P<id>[A-Za-z0-9]+)(?:/.*)?$"
)


def normalize_ark(value: str) -> str:
    """Return the Gallica identifier portion of an ARK.

    Accepted examples include ``bpt6k5738219s``, ``ark:/12148/bpt6k5738219s``
    and canonical Gallica ARK URLs such as
    ``https://gallica.bnf.fr/ark:/12148/bpt6k5738219s/f3.image``.

    A Gallica URL that carries no ``ark:/12148/`` marker is rejected rather than
    reduced to its first path segment.
    """
    candidate = value.strip()
    match = _ARK_RE.fullmatch(candidate)
    if match is None:
        raise ValueError(
            f"Invalid Gallica ARK: {value!r}; expected a bare identifier, "
            "'ark:/12148/<id>', or a Gallica URL containing 'ark:/12148/<id>'"
        )
    return match.group("id")


def ark_uri(value: str) -> str:
    """Return a canonical ``ark:/12148/...`` URI."""
    return f"ark:/12148/{normalize_ark(value)}"

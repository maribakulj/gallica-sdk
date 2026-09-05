class GallicaError(Exception):
    """Base exception for errors detected by gallica-sdk."""


class GallicaResponseError(GallicaError):
    """Raised when Gallica returns an HTTP success with an invalid payload."""

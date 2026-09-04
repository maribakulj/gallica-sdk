from importlib.metadata import PackageNotFoundError, version


def package_version() -> str:
    """Return the installed distribution version, with a source-tree fallback."""
    try:
        return version("gallica-sdk")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = package_version()

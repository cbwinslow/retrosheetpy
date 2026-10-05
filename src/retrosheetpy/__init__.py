"""Download Retrosheet seasons, cache them, and turn them into data tables."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("retrosheetpy")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0.0.0"

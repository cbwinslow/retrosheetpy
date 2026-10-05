"""Package version, kept apart so any module can read it without a circular import."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("retrosheetpy")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0.0.0"

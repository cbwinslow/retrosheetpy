"""Download Retrosheet seasons, cache them, and turn them into data tables."""

from retrosheetpy._meta import __version__
from retrosheetpy.artifact import Artifact
from retrosheetpy.catalog import Product, Resource, resolve
from retrosheetpy.client import Client, http_fetch, iter_zip_members
from retrosheetpy.errors import (
    ArchiveTooLargeError,
    IntegrityError,
    InvalidArchiveError,
    RetrosheetError,
    UnsafeArchiveMemberError,
)
from retrosheetpy.season import Season, cache_dir, get

__all__ = [
    "ArchiveTooLargeError",
    "Artifact",
    "Client",
    "IntegrityError",
    "InvalidArchiveError",
    "Product",
    "Resource",
    "RetrosheetError",
    "Season",
    "UnsafeArchiveMemberError",
    "__version__",
    "cache_dir",
    "get",
    "http_fetch",
    "iter_zip_members",
    "resolve",
]

"""Download Retrosheet seasons, cache them, and turn them into data tables."""

from retrosheetpy._meta import __version__
from retrosheetpy.artifact import Artifact
from retrosheetpy.catalog import Product, Resource, resolve
from retrosheetpy.client import Client, http_fetch, iter_zip_members
from retrosheetpy.errors import (
    IntegrityError,
    InvalidArchiveError,
    RetrosheetError,
    UnsafeArchiveMemberError,
)

__all__ = [
    "Artifact",
    "Client",
    "IntegrityError",
    "InvalidArchiveError",
    "Product",
    "Resource",
    "RetrosheetError",
    "UnsafeArchiveMemberError",
    "__version__",
    "http_fetch",
    "iter_zip_members",
    "resolve",
]

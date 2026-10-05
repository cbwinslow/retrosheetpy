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
    ToolError,
    UnsafeArchiveMemberError,
)
from retrosheetpy.season import Season, cache_dir, get
from retrosheetpy.tables import boxscores, comments, daily, events, games, subs

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
    "ToolError",
    "UnsafeArchiveMemberError",
    "__version__",
    "boxscores",
    "cache_dir",
    "comments",
    "daily",
    "events",
    "games",
    "get",
    "http_fetch",
    "iter_zip_members",
    "resolve",
    "subs",
]

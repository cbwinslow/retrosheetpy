"""Download Retrosheet seasons, cache them, and turn them into data tables.

import retrosheetpy as rs

rs.events(2010)                        # every play of 2010, a Table (streams; 164 columns)
rs.games(range(2000, 2011), home="NYA")  # several seasons, one team's home games
rs.season(2010).daily().to_csv("daily.csv")
rs.events(2010).to_sqlite("mlb.db")
"""

from retrosheetpy._meta import __version__
from retrosheetpy.api import (
    Field,
    boxscores,
    comments,
    daily,
    events,
    fields,
    games,
    season,
    subs,
)
from retrosheetpy.artifact import Artifact
from retrosheetpy.cache import Season, cache_dir, cached_seasons
from retrosheetpy.cache import clear as clear_cache
from retrosheetpy.cache import verify as verify_cache
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
from retrosheetpy.options import Opts
from retrosheetpy.table import BoxScores, Table

__all__ = [
    "ArchiveTooLargeError",
    "Artifact",
    "BoxScores",
    "Client",
    "Field",
    "IntegrityError",
    "InvalidArchiveError",
    "Opts",
    "Product",
    "Resource",
    "RetrosheetError",
    "Season",
    "Table",
    "ToolError",
    "UnsafeArchiveMemberError",
    "__version__",
    "boxscores",
    "cache_dir",
    "cached_seasons",
    "clear_cache",
    "comments",
    "daily",
    "events",
    "fields",
    "games",
    "http_fetch",
    "iter_zip_members",
    "resolve",
    "season",
    "subs",
    "verify_cache",
]

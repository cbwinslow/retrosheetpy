"""retrosheetpy - Fast, strongly-typed Retrosheet downloader, parser, and database ingestor."""

from retrosheetpy._meta import __version__
from retrosheetpy.api import (
    allstar,
    bio,
    download,
    ejections,
    events,
    game_logs,
    get_ddl,
    parks,
    postseason,
    rosters,
    schedules,
    to_dlt,
    to_duckdb,
    to_parquet,
    transactions,
)

__all__ = [
    "__version__",
    "allstar",
    "bio",
    "download",
    "ejections",
    "events",
    "game_logs",
    "get_ddl",
    "parks",
    "postseason",
    "rosters",
    "schedules",
    "to_dlt",
    "to_duckdb",
    "to_parquet",
    "transactions",
]

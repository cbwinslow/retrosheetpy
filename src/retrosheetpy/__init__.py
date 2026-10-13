"""retrosheetpy - Fast, strongly-typed Retrosheet downloader, parser, and database ingestor."""

from retrosheetpy._meta import __version__
from retrosheetpy.api import (
    events,
    game_logs,
    get_ddl,
    parks,
    rosters,
    to_dlt,
    to_duckdb,
    to_parquet,
)

__all__ = [
    "__version__",
    "events",
    "game_logs",
    "get_ddl",
    "parks",
    "rosters",
    "to_dlt",
    "to_duckdb",
    "to_parquet",
]

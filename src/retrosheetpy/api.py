"""High-level user-facing API for retrosheetpy."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pyarrow as pa

from retrosheetpy.extract.downloader import Downloader
from retrosheetpy.parse.events import EventParser
from retrosheetpy.parse.gamelogs import GameLogParser
from retrosheetpy.parse.parks import ParkParser
from retrosheetpy.parse.rosters import RosterParser
from retrosheetpy.sink.dataframe import to_arrow, to_pandas, to_polars
from retrosheetpy.sink.duckdb_sink import DuckDBSink
from retrosheetpy.sink.file_sink import FileSink


def _convert_backend(table: pa.Table, backend: str) -> Any:
    b = backend.lower()
    if b == "arrow":
        return to_arrow(table)
    if b == "polars":
        return to_polars(table)
    if b == "pandas":
        return to_pandas(table)
    raise ValueError(f"Unknown backend '{backend}'. Choose from 'arrow', 'polars', or 'pandas'.")


def _normalize_years(years: int | Sequence[int]) -> list[int]:
    if isinstance(years, int):
        return [years]
    return list(years)


def events(
    year: int | Sequence[int],
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
) -> Any:
    """Downloads, parses, and returns play-by-play events as a strongly-typed DataFrame or Arrow Table."""
    dl = downloader or Downloader()
    parser = EventParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_events(y, force=force)
        # Find all .EVA and .EVN files
        files = sorted(list(extracted_dir.glob("*.EVA")) + list(extracted_dir.glob("*.EVN")))
        if files:
            tbl = parser.parse_files(files, year=y)
            tables.append(tbl)

    if not tables:
        from retrosheetpy.schemas.events import EVENT_SCHEMA

        consolidated = pa.Table.from_batches([], schema=EVENT_SCHEMA)
    else:
        consolidated = pa.concat_tables(tables)

    return _convert_backend(consolidated, backend)


def game_logs(
    year: int | Sequence[int],
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
) -> Any:
    """Downloads, parses, and returns official game logs as a strongly-typed DataFrame or Arrow Table."""
    dl = downloader or Downloader()
    parser = GameLogParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_gamelogs(y, force=force)
        gl_files = list(extracted_dir.glob("gl*.txt"))
        if gl_files:
            tbl = parser.parse_files(gl_files)
            tables.append(tbl)

    if not tables:
        from retrosheetpy.schemas.gamelogs import GAMELOG_SCHEMA

        consolidated = pa.Table.from_batches([], schema=GAMELOG_SCHEMA)
    else:
        consolidated = pa.concat_tables(tables)

    return _convert_backend(consolidated, backend)


def rosters(
    year: int | Sequence[int],
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
) -> Any:
    """Downloads event archives to parse and return team rosters as a strongly-typed table."""
    dl = downloader or Downloader()
    parser = RosterParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_events(y, force=force)
        ros_files = list(extracted_dir.glob("*.ROS"))
        if ros_files:
            tbl = parser.parse_files(ros_files, year=y)
            tables.append(tbl)

    if not tables:
        from retrosheetpy.schemas.rosters import ROSTER_SCHEMA

        consolidated = pa.Table.from_batches([], schema=ROSTER_SCHEMA)
    else:
        consolidated = pa.concat_tables(tables)

    return _convert_backend(consolidated, backend)


def parks(
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
) -> Any:
    """Downloads and returns the official ballpark encyclopedia table."""
    dl = downloader or Downloader()
    parser = ParkParser()
    file_path = dl.get_parks(force=force)
    table = parser.parse_file(file_path)
    return _convert_backend(table, backend)


def to_duckdb(
    path: Path | str,
    years: int | Sequence[int],
    datasets: Sequence[str] = ("events", "gamelogs", "rosters", "parks"),
    force: bool = False,
    downloader: Downloader | None = None,
) -> None:
    """Ingests selected Retrosheet datasets into a DuckDB database."""
    dl = downloader or Downloader()
    sink = DuckDBSink(db_path=path)

    try:
        ds_set = set(d.lower() for d in datasets)

        if "parks" in ds_set:
            tbl_parks = parks(backend="arrow", force=force, downloader=dl)
            sink.write_table("parks", tbl_parks)

        if "gamelogs" in ds_set or "game_logs" in ds_set:
            tbl_gl = game_logs(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("game_logs", tbl_gl)

        if "rosters" in ds_set:
            tbl_rosters = rosters(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("rosters", tbl_rosters)

        if "events" in ds_set:
            tbl_events = events(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("events", tbl_events)
    finally:
        sink.close()


def to_parquet(
    path: Path | str,
    dataset: str,
    years: int | Sequence[int] = 2024,
    force: bool = False,
    downloader: Downloader | None = None,
) -> Path:
    """Exports a specified dataset into a Parquet file."""
    dl = downloader or Downloader()
    sink = FileSink()
    d = dataset.lower()

    if d == "events":
        tbl = events(year=years, backend="arrow", force=force, downloader=dl)
    elif d in ("gamelogs", "game_logs"):
        tbl = game_logs(year=years, backend="arrow", force=force, downloader=dl)
    elif d == "rosters":
        tbl = rosters(year=years, backend="arrow", force=force, downloader=dl)
    elif d == "parks":
        tbl = parks(backend="arrow", force=force, downloader=dl)
    else:
        raise ValueError(f"Unsupported dataset: {dataset}")

    return sink.write_parquet(path, tbl)


def get_ddl(dataset: str, dialect: str = "postgres") -> str:
    """Returns the SQL DDL CREATE TABLE statement for a given dataset and dialect."""
    from retrosheetpy.schemas.ddl import generate_ddl

    return generate_ddl(dataset, dialect=dialect)


def to_dlt(
    destination: str | Any,
    years: int | Sequence[int],
    datasets: Sequence[str] = ("events", "gamelogs", "rosters", "parks"),
    pipeline_name: str = "retrosheet",
    downloader: Downloader | None = None,
    **dlt_kwargs: Any,
) -> Any:
    """Runs a full dlt pipeline ingesting Retrosheet datasets into Postgres, Snowflake, BigQuery, etc."""
    try:
        import dlt
    except ImportError as err:
        raise ImportError(
            "dlt is not installed. Install it via 'pip install retrosheetpy[dlt]' or 'pip install dlt'."
        ) from err

    from retrosheetpy.sink.dlt_sink import retrosheet_source

    pipeline = dlt.pipeline(pipeline_name=pipeline_name, destination=destination, **dlt_kwargs)
    source = retrosheet_source(years=years, datasets=datasets, downloader=downloader)
    return pipeline.run(source)


def download(
    years: int | Sequence[int] | None = None,
    datasets: Sequence[str] | str = "all",
    force: bool = False,
    downloader: Downloader | None = None,
) -> dict[str, list[Path]]:
    """Downloads specified Retrosheet archives to local cache without loading them into memory.

    Args:
        years: Year or sequence of years to download. Defaults to [2024] if not provided.
        datasets: Dataset or comma-separated list of datasets to download
            ('events', 'gamelogs', 'rosters', 'parks', 'schedules', 'bio', or 'all').
        force: If True, re-downloads even if already cached.
        downloader: Optional custom Downloader instance.

    Returns:
        Dictionary mapping dataset name to list of extracted paths or file locations.
    """
    dl = downloader or Downloader()
    results: dict[str, list[Path]] = {}

    if isinstance(datasets, str):
        if datasets.lower() == "all":
            dataset_list = ["events", "gamelogs", "parks", "schedules", "bio"]
        else:
            dataset_list = [d.strip().lower() for d in datasets.split(",")]
    else:
        dataset_list = [d.lower() for d in datasets]

    year_list = _normalize_years(years) if years is not None else [2024]

    for d in dataset_list:
        results[d] = []
        if d in ("events", "rosters"):
            for y in year_list:
                p = dl.get_events(y, force=force)
                results[d].append(p)
        elif d in ("gamelogs", "game_logs"):
            for y in year_list:
                p = dl.get_gamelogs(y, force=force)
                results[d].append(p)
        elif d == "schedules":
            for y in year_list:
                p = dl.get_schedules(y, force=force)
                results[d].append(p)
        elif d == "parks":
            p = dl.get_parks(force=force)
            results[d].append(p)
        elif d == "bio":
            p = dl.get_bio(force=force)
            results[d].append(p)

    return results

"""High-level user-facing API for retrosheetpy."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import pyarrow as pa

from retrosheetpy.extract.config import DownloaderConfig
from retrosheetpy.extract.downloader import Downloader
from retrosheetpy.parse.bio import BioParser
from retrosheetpy.parse.ejections import EjectionParser
from retrosheetpy.parse.events import EventParser
from retrosheetpy.parse.gamelogs import GameLogParser
from retrosheetpy.parse.parks import ParkParser
from retrosheetpy.parse.rosters import RosterParser
from retrosheetpy.parse.schedules import ScheduleParser
from retrosheetpy.parse.transactions import TransactionParser
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


def _resolve_downloader(
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Downloader:
    """Helper to instantiate or configure a Downloader with the desired source."""
    if downloader is not None:
        if source is not None:
            downloader.source = source
        return downloader
    return Downloader(config=DownloaderConfig(source=source or "github"))


def events(
    year: int | Sequence[int],
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads, parses, and returns play-by-play events as a strongly-typed DataFrame or Arrow Table."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = EventParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_events(y, force=force)
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


def postseason(
    year: int | Sequence[int],
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads, parses, and returns postseason play-by-play events."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = EventParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_postseason(y, force=force)
        files = sorted(
            list(extracted_dir.glob("*.EVA"))
            + list(extracted_dir.glob("*.EVN"))
            + list(extracted_dir.glob("*.EVE"))
        )
        if files:
            tbl = parser.parse_files(files, year=y)
            tables.append(tbl)

    if not tables:
        from retrosheetpy.schemas.events import EVENT_SCHEMA

        consolidated = pa.Table.from_batches([], schema=EVENT_SCHEMA)
    else:
        consolidated = pa.concat_tables(tables)

    return _convert_backend(consolidated, backend)


def allstar(
    year: int | Sequence[int],
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads, parses, and returns All-Star Game play-by-play events."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = EventParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_allstar(y, force=force)
        files = sorted(
            list(extracted_dir.glob("*.EVA"))
            + list(extracted_dir.glob("*.EVN"))
            + list(extracted_dir.glob("*.EVE"))
        )
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
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads, parses, and returns official game logs as a strongly-typed DataFrame or Arrow Table."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = GameLogParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_gamelogs(y, force=force)
        gl_files = sorted(list(extracted_dir.glob("*.[tT][xX][tT]")))
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
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads, parses, and returns annual team roster files (.ROS)."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = RosterParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_events(y, force=force)
        ros_files = sorted(list(extracted_dir.glob("*.ROS")))
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
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads and returns the official Retrosheet ballpark directory."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = ParkParser()
    file_path = dl.get_parks(force=force)
    table = parser.parse_file(file_path)
    return _convert_backend(table, backend)


def schedules(
    year: int | Sequence[int] = 2024,
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads, parses, and returns official regular season game schedules."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = ScheduleParser()
    year_list = _normalize_years(year)
    tables: list[pa.Table] = []

    for y in year_list:
        extracted_dir = dl.get_schedules(y, force=force)
        sched_files = sorted(
            list(extracted_dir.glob("*schedule*.csv"))
            + list(extracted_dir.glob("*.csv"))
            + list(extracted_dir.glob("*.txt"))
        )
        if sched_files:
            tbl = parser.parse_file(sched_files[0])
            tables.append(tbl)

    if not tables:
        from retrosheetpy.schemas.schedules import SCHEDULE_SCHEMA

        consolidated = pa.Table.from_batches([], schema=SCHEDULE_SCHEMA)
    else:
        consolidated = pa.concat_tables(tables)

    return _convert_backend(consolidated, backend)


def bio(
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads and returns the master player and personnel biographical database."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = BioParser()
    file_path = dl.get_bio(force=force)
    table = parser.parse_file(file_path)
    return _convert_backend(table, backend)


def ejections(
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads and returns the official ejections database."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = EjectionParser()
    file_path = dl.get_ejections(force=force)
    table = parser.parse_file(file_path)
    return _convert_backend(table, backend)


def transactions(
    backend: str = "arrow",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Any:
    """Downloads and returns the historical player transactions database.

    Note: Upstream Retrosheet discontinued updating transactions on November 26, 2021,
    transitioning ongoing maintenance to Baseball-Reference.
    """
    dl = _resolve_downloader(downloader=downloader, source=source)
    parser = TransactionParser()
    file_path = dl.get_transactions(force=force)
    table = parser.parse_file(file_path)
    return _convert_backend(table, backend)


def to_duckdb(
    path: Path | str,
    years: int | Sequence[int] = 2024,
    datasets: Sequence[str] = ("events", "gamelogs", "rosters", "parks"),
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> None:
    """Ingests selected Retrosheet datasets into a DuckDB database."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    sink = DuckDBSink(db_path=path)

    try:
        ds_set = set(d.lower() for d in datasets)

        if "parks" in ds_set:
            tbl_parks = parks(backend="arrow", force=force, downloader=dl)
            sink.write_table("parks", tbl_parks)

        if "bio" in ds_set:
            tbl_bio = bio(backend="arrow", force=force, downloader=dl)
            sink.write_table("biographical", tbl_bio)

        if "ejections" in ds_set:
            tbl_ej = ejections(backend="arrow", force=force, downloader=dl)
            sink.write_table("ejections", tbl_ej)

        if "transactions" in ds_set:
            try:
                tbl_tr = transactions(backend="arrow", force=force, downloader=dl)
                sink.write_table("transactions", tbl_tr)
            except FileNotFoundError as err:
                warnings.warn(
                    f"Skipping transactions dataset in DuckDB ingestion: {err}",
                    UserWarning,
                    stacklevel=2,
                )

        if "schedules" in ds_set:
            tbl_sked = schedules(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("schedules", tbl_sked)

        if "gamelogs" in ds_set or "game_logs" in ds_set:
            tbl_gl = game_logs(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("game_logs", tbl_gl)

        if "rosters" in ds_set:
            tbl_rosters = rosters(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("rosters", tbl_rosters)

        if "events" in ds_set:
            tbl_events = events(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("events", tbl_events)

        if "postseason" in ds_set:
            tbl_post = postseason(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("postseason_events", tbl_post)

        if "allstar" in ds_set:
            tbl_as = allstar(year=years, backend="arrow", force=force, downloader=dl)
            sink.write_table("allstar_events", tbl_as)
    finally:
        sink.close()


def to_parquet(
    path: Path | str,
    dataset: str,
    years: int | Sequence[int] = 2024,
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> Path:
    """Exports a specific Retrosheet dataset to a Parquet file."""
    dl = _resolve_downloader(downloader=downloader, source=source)
    sink = FileSink()

    d = dataset.lower()
    if d == "events":
        tbl = events(year=years, backend="arrow", force=force, downloader=dl)
    elif d == "postseason":
        tbl = postseason(year=years, backend="arrow", force=force, downloader=dl)
    elif d == "allstar":
        tbl = allstar(year=years, backend="arrow", force=force, downloader=dl)
    elif d in ("gamelogs", "game_logs"):
        tbl = game_logs(year=years, backend="arrow", force=force, downloader=dl)
    elif d == "rosters":
        tbl = rosters(year=years, backend="arrow", force=force, downloader=dl)
    elif d == "parks":
        tbl = parks(backend="arrow", force=force, downloader=dl)
    elif d == "schedules":
        tbl = schedules(year=years, backend="arrow", force=force, downloader=dl)
    elif d == "bio":
        tbl = bio(backend="arrow", force=force, downloader=dl)
    elif d == "ejections":
        tbl = ejections(backend="arrow", force=force, downloader=dl)
    elif d == "transactions":
        tbl = transactions(backend="arrow", force=force, downloader=dl)
    else:
        raise ValueError(f"Unsupported dataset: {dataset}")

    return sink.write_parquet(path, tbl)


def get_ddl(dataset: str, dialect: str = "postgres") -> str:
    """Returns the SQL DDL CREATE TABLE statement for a given dataset and dialect."""
    from retrosheetpy.schemas.ddl import generate_ddl

    return generate_ddl(dataset, dialect=dialect)


def to_dlt(
    destination: str | Any,
    years: int | Sequence[int] = 2024,
    datasets: Sequence[str] = ("events", "gamelogs", "rosters", "parks"),
    pipeline_name: str = "retrosheet",
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
    **dlt_kwargs: Any,
) -> Any:
    """Runs a full dlt pipeline ingesting Retrosheet datasets into Postgres, Snowflake, DuckDB, etc."""
    try:
        import dlt
    except ImportError as err:
        raise ImportError("dlt is not installed. Install it via 'pip install dlt'.") from err

    from retrosheetpy.sink.dlt_sink import retrosheet_source

    dl = _resolve_downloader(downloader=downloader, source=source)
    pipeline = dlt.pipeline(pipeline_name=pipeline_name, destination=destination, **dlt_kwargs)
    src = retrosheet_source(years=years, datasets=datasets, downloader=dl)
    return pipeline.run(src)


def download(
    years: int | Sequence[int] | None = None,
    datasets: Sequence[str] | str = "all",
    force: bool = False,
    downloader: Downloader | None = None,
    source: Literal["github", "retrosheet", "auto"] | None = None,
) -> dict[str, list[Path]]:
    """Downloads specified Retrosheet archives to local cache without loading them into memory.

    Args:
        years: Year or sequence of years to download. Defaults to [2024] if not provided.
        datasets: Dataset or comma-separated list of datasets to download
            ('events', 'postseason', 'allstar', 'gamelogs', 'rosters', 'parks',
             'schedules', 'bio', 'ejections', 'transactions', or 'all').
        force: If True, re-downloads even if already cached.
        downloader: Optional custom Downloader instance.
        source: Optional source override ('github', 'retrosheet', or 'auto').

    Returns:
        Dictionary mapping dataset name to list of extracted paths or file locations.
    """
    dl = _resolve_downloader(downloader=downloader, source=source)
    results: dict[str, list[Path]] = {}

    all_supported = [
        "events",
        "postseason",
        "allstar",
        "gamelogs",
        "rosters",
        "parks",
        "schedules",
        "bio",
        "ejections",
        "transactions",
    ]

    if isinstance(datasets, str):
        if datasets.lower() == "all":
            selected = all_supported
        else:
            selected = [d.strip().lower() for d in datasets.split(",") if d.strip()]
    else:
        selected = [d.lower() for d in datasets]

    year_list = _normalize_years(years) if years is not None else [2024]

    for d in selected:
        results[d] = []
        if d == "events":
            for y in year_list:
                p = dl.get_events(y, force=force)
                results[d].append(p)
        elif d == "postseason":
            for y in year_list:
                p = dl.get_postseason(y, force=force)
                results[d].append(p)
        elif d == "allstar":
            for y in year_list:
                p = dl.get_allstar(y, force=force)
                results[d].append(p)
        elif d in ("gamelogs", "game_logs"):
            for y in year_list:
                p = dl.get_gamelogs(y, force=force)
                results[d].append(p)
        elif d == "rosters":
            for y in year_list:
                p = dl.get_events(y, force=force)
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
        elif d == "ejections":
            p = dl.get_ejections(force=force)
            results[d].append(p)
        elif d == "transactions":
            try:
                p = dl.get_transactions(force=force)
                results[d].append(p)
            except FileNotFoundError as err:
                warnings.warn(
                    f"Skipping transactions download: {err}",
                    UserWarning,
                    stacklevel=2,
                )

    return results

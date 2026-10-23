"""dlt (data load tool) source for loading Retrosheet into cloud data warehouses."""

from __future__ import annotations

import warnings
from collections.abc import Iterator, Sequence
from typing import Any

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


def retrosheet_source(
    years: int | Sequence[int] = 2024,
    datasets: Sequence[str] = ("events", "gamelogs", "rosters", "parks"),
    downloader: Downloader | None = None,
    source_type: str | None = None,
) -> Any:
    """Creates a dlt source yielding PyArrow Tables for ingestion into Snowflake, Postgres, DuckDB, etc."""
    try:
        import dlt
    except ImportError as err:
        raise ImportError(
            "dlt is not installed. Install it via 'pip install retrosheetpy[dlt]' or 'pip install dlt'."
        ) from err

    dl = downloader or Downloader(config=DownloaderConfig(source=source_type or "github"))  # type: ignore[arg-type]
    year_list = [years] if isinstance(years, int) else list(years)
    selected_datasets = set(d.lower() for d in datasets)

    @dlt.source(name="retrosheet")
    def _source() -> Iterator[Any]:
        if "parks" in selected_datasets:

            @dlt.resource(name="parks", write_disposition="replace")
            def _parks_resource() -> Iterator[pa.Table]:
                parser = ParkParser()
                path = dl.get_parks()
                tbl = parser.parse_file(path)
                if tbl.num_rows > 0:
                    yield tbl

            yield _parks_resource

        if "bio" in selected_datasets:

            @dlt.resource(name="biographical", write_disposition="replace")
            def _bio_resource() -> Iterator[pa.Table]:
                parser = BioParser()
                path = dl.get_bio()
                tbl = parser.parse_file(path)
                if tbl.num_rows > 0:
                    yield tbl

            yield _bio_resource

        if "ejections" in selected_datasets:

            @dlt.resource(name="ejections", write_disposition="replace")
            def _ejections_resource() -> Iterator[pa.Table]:
                parser = EjectionParser()
                path = dl.get_ejections()
                tbl = parser.parse_file(path)
                if tbl.num_rows > 0:
                    yield tbl

            yield _ejections_resource

        if "transactions" in selected_datasets:

            @dlt.resource(name="transactions", write_disposition="replace")
            def _transactions_resource() -> Iterator[pa.Table]:
                parser = TransactionParser()
                try:
                    path = dl.get_transactions()
                    tbl = parser.parse_file(path)
                    if tbl.num_rows > 0:
                        yield tbl
                except FileNotFoundError as err:
                    warnings.warn(
                        f"Skipping dlt transactions resource: {err}",
                        UserWarning,
                        stacklevel=2,
                    )

            yield _transactions_resource

        if "schedules" in selected_datasets:

            @dlt.resource(
                name="schedules",
                write_disposition="merge",
                primary_key=["date", "home_team", "game_num"],
            )
            def _schedules_resource() -> Iterator[pa.Table]:
                parser = ScheduleParser()
                for y in year_list:
                    extracted_dir = dl.get_schedules(y)
                    sched_files = sorted(
                        list(extracted_dir.glob("*schedule*.csv"))
                        + list(extracted_dir.glob("*.csv"))
                        + list(extracted_dir.glob("*.txt"))
                    )
                    if sched_files:
                        tbl = parser.parse_file(sched_files[0])
                        if tbl.num_rows > 0:
                            yield tbl

            yield _schedules_resource

        if "gamelogs" in selected_datasets or "game_logs" in selected_datasets:

            @dlt.resource(
                name="game_logs",
                write_disposition="merge",
                primary_key=["date", "home_team", "game_number"],
            )
            def _gamelogs_resource() -> Iterator[pa.Table]:
                parser = GameLogParser()
                for y in year_list:
                    extracted_dir = dl.get_gamelogs(y)
                    for gl_file in sorted(extracted_dir.glob("*.[tT][xX][tT]")):
                        tbl = parser.parse_file(gl_file)
                        if tbl.num_rows > 0:
                            yield tbl

            yield _gamelogs_resource

        if "rosters" in selected_datasets:

            @dlt.resource(
                name="rosters",
                write_disposition="merge",
                primary_key=["year", "team_id", "player_id"],
            )
            def _rosters_resource() -> Iterator[pa.Table]:
                parser = RosterParser()
                for y in year_list:
                    extracted_dir = dl.get_events(y)
                    for ros_file in sorted(extracted_dir.glob("*.ROS")):
                        tbl = parser.parse_file(ros_file, year=y)
                        if tbl.num_rows > 0:
                            yield tbl

            yield _rosters_resource

        if "events" in selected_datasets:

            @dlt.resource(
                name="events",
                write_disposition="merge",
                primary_key=["game_id", "event_id"],
            )
            def _events_resource() -> Iterator[pa.Table]:
                parser = EventParser()
                for y in year_list:
                    extracted_dir = dl.get_events(y)
                    files = sorted(
                        list(extracted_dir.glob("*.EVA")) + list(extracted_dir.glob("*.EVN"))
                    )
                    if files:
                        tbl = parser.parse_files(files, year=y)
                        if tbl.num_rows > 0:
                            yield tbl

            yield _events_resource

        if "postseason" in selected_datasets:

            @dlt.resource(
                name="postseason_events",
                write_disposition="merge",
                primary_key=["game_id", "event_id"],
            )
            def _postseason_resource() -> Iterator[pa.Table]:
                parser = EventParser()
                for y in year_list:
                    extracted_dir = dl.get_postseason(y)
                    files = sorted(
                        list(extracted_dir.glob("*.EVA"))
                        + list(extracted_dir.glob("*.EVN"))
                        + list(extracted_dir.glob("*.EVE"))
                    )
                    if files:
                        tbl = parser.parse_files(files, year=y)
                        if tbl.num_rows > 0:
                            yield tbl

            yield _postseason_resource

        if "allstar" in selected_datasets:

            @dlt.resource(
                name="allstar_events",
                write_disposition="merge",
                primary_key=["game_id", "event_id"],
            )
            def _allstar_resource() -> Iterator[pa.Table]:
                parser = EventParser()
                for y in year_list:
                    extracted_dir = dl.get_allstar(y)
                    files = sorted(
                        list(extracted_dir.glob("*.EVA"))
                        + list(extracted_dir.glob("*.EVN"))
                        + list(extracted_dir.glob("*.EVE"))
                    )
                    if files:
                        tbl = parser.parse_files(files, year=y)
                        if tbl.num_rows > 0:
                            yield tbl

            yield _allstar_resource

    return _source()

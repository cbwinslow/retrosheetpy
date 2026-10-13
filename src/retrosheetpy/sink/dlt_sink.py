"""Optional dlt (data load tool) source for loading Retrosheet into cloud data warehouses."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from retrosheetpy.extract.downloader import Downloader
from retrosheetpy.parse.events import EventParser
from retrosheetpy.parse.gamelogs import GameLogParser
from retrosheetpy.parse.parks import ParkParser
from retrosheetpy.parse.rosters import RosterParser


def retrosheet_source(
    years: int | Sequence[int],
    datasets: Sequence[str] = ("events", "gamelogs", "rosters", "parks"),
    downloader: Downloader | None = None,
) -> Any:
    """Creates a dlt source for ingesting Retrosheet datasets into Snowflake, Postgres, BigQuery, etc."""
    try:
        import dlt
    except ImportError as err:
        raise ImportError(
            "dlt is not installed. Install it via 'pip install retrosheetpy[dlt]' or 'pip install dlt'."
        ) from err

    dl = downloader or Downloader()
    year_list = [years] if isinstance(years, int) else list(years)
    selected_datasets = set(d.lower() for d in datasets)

    @dlt.source(name="retrosheet")
    def _source() -> Iterator[Any]:
        if "parks" in selected_datasets:

            @dlt.resource(name="parks", write_disposition="replace")
            def _parks_resource() -> Iterator[dict[str, Any]]:
                parser = ParkParser()
                path = dl.get_parks()
                tbl = parser.parse_file(path)
                for batch in tbl.to_batches():
                    yield from batch.to_pylist()

            yield _parks_resource

        if "gamelogs" in selected_datasets or "game_logs" in selected_datasets:

            @dlt.resource(name="game_logs", write_disposition="append")
            def _gamelogs_resource() -> Iterator[dict[str, Any]]:
                parser = GameLogParser()
                for y in year_list:
                    extracted_dir = dl.get_gamelogs(y)
                    for gl_file in extracted_dir.glob("gl*.txt"):
                        tbl = parser.parse_file(gl_file)
                        for batch in tbl.to_batches():
                            yield from batch.to_pylist()

            yield _gamelogs_resource

        if "rosters" in selected_datasets:

            @dlt.resource(name="rosters", write_disposition="append")
            def _rosters_resource() -> Iterator[dict[str, Any]]:
                parser = RosterParser()
                for y in year_list:
                    extracted_dir = dl.get_events(y)
                    for ros_file in extracted_dir.glob("*.ROS"):
                        tbl = parser.parse_file(ros_file, year=y)
                        for batch in tbl.to_batches():
                            yield from batch.to_pylist()

            yield _rosters_resource

        if "events" in selected_datasets:

            @dlt.resource(name="events", write_disposition="append")
            def _events_resource() -> Iterator[dict[str, Any]]:
                parser = EventParser()
                for y in year_list:
                    extracted_dir = dl.get_events(y)
                    files = sorted(
                        list(extracted_dir.glob("*.EVA")) + list(extracted_dir.glob("*.EVN"))
                    )
                    for f in files:
                        yield from parser.parse_file_rows(f)

            yield _events_resource

    return _source()

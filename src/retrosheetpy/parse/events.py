"""Bridge to chadwickpy for parsing Retrosheet play-by-play event files into typed PyArrow Tables."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pyarrow as pa
from chadwickpy.roster import League
from chadwickpy.tools.events import event_rows

from retrosheetpy.schemas.events import EVENT_SCHEMA, cast_event_row


class EventParser:
    """Parses Retrosheet play-by-play event files (.EVA, .EVN) into strongly-typed PyArrow Tables."""

    def __init__(self, league: League | None = None) -> None:
        self.league = league

    def parse_file_rows(self, path: Path) -> Iterator[dict[str, object]]:
        """Yields typed event row dictionaries for a single event file."""
        data = path.read_bytes()
        for raw_row in event_rows(data, league=self.league):
            yield cast_event_row(raw_row)

    def parse_files(self, paths: list[Path], year: int | None = None) -> pa.Table:
        """Parses multiple event files and outputs a consolidated typed PyArrow Table."""
        # Try to initialize League if rosters exist in the same directory
        league = self.league
        if league is None and paths:
            parent = paths[0].parent
            team_file = parent / f"TEAM{year}" if year else None
            if team_file and team_file.exists():
                try:
                    league = League()
                    league.read(team_file.read_bytes())
                except Exception:
                    league = None

        records: list[dict[str, object]] = []
        for path in paths:
            data = path.read_bytes()
            for raw_row in event_rows(data, league=league):
                records.append(cast_event_row(raw_row))

        if not records:
            return pa.Table.from_batches([], schema=EVENT_SCHEMA)

        arrays = []
        for field in EVENT_SCHEMA:
            col_name = field.name
            col_type = field.type
            col_vals = [r.get(col_name) for r in records]
            arrays.append(pa.array(col_vals, type=col_type))

        return pa.Table.from_arrays(arrays, schema=EVENT_SCHEMA)

"""Parser for Retrosheet Roster files (.ROS)."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa

from retrosheetpy.schemas.rosters import ROSTER_SCHEMA, parse_roster_line


class RosterParser:
    """Parses Retrosheet roster files (.ROS) into strongly-typed PyArrow Tables."""

    def parse_file(self, path: Path, year: int | None = None) -> pa.Table:
        """Parses a single .ROS roster file."""
        return self.parse_files([path], year=year)

    def parse_files(self, paths: list[Path], year: int | None = None) -> pa.Table:
        """Parses multiple .ROS roster files into a single Arrow Table."""
        records: list[dict[str, object]] = []
        for path in paths:
            # e.g. NYA2024.ROS -> team_id = NYA
            stem = path.stem
            team_id = stem[:3] if len(stem) >= 3 else ""
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        records.append(parse_roster_line(s, year=year, team_id=team_id))

        if not records:
            return pa.Table.from_batches([], schema=ROSTER_SCHEMA)

        arrays = []
        for field in ROSTER_SCHEMA:
            col_name = field.name
            col_type = field.type
            col_vals = [r.get(col_name) for r in records]
            arrays.append(pa.array(col_vals, type=col_type))

        return pa.Table.from_arrays(arrays, schema=ROSTER_SCHEMA)

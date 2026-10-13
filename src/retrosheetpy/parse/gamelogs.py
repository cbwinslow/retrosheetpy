"""Parser for Retrosheet Game Logs (glYYYY.txt)."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa

from retrosheetpy.schemas.gamelogs import GAMELOG_SCHEMA, parse_gamelog_line


class GameLogParser:
    """Parses Retrosheet game logs into strongly-typed PyArrow Tables."""

    def parse_file(self, path: Path) -> pa.Table:
        """Parses a game log file into an Arrow Table conforming to GAMELOG_SCHEMA."""
        records: list[dict[str, object]] = []
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                s = line.strip()
                if s:
                    records.append(parse_gamelog_line(s))

        if not records:
            return pa.Table.from_batches([], schema=GAMELOG_SCHEMA)

        # Convert list of dicts to columnar pyarrow Table
        arrays = []
        for field in GAMELOG_SCHEMA:
            col_name = field.name
            col_type = field.type
            col_vals = [r.get(col_name) for r in records]
            arrays.append(pa.array(col_vals, type=col_type))

        return pa.Table.from_arrays(arrays, schema=GAMELOG_SCHEMA)

    def parse_files(self, paths: list[Path]) -> pa.Table:
        """Parses multiple game log files and concatenates them into a single table."""
        tables = [self.parse_file(p) for p in paths]
        if not tables:
            return pa.Table.from_batches([], schema=GAMELOG_SCHEMA)
        return pa.concat_tables(tables)

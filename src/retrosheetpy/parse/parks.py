"""Parser for Retrosheet Ballparks (parkcode.txt)."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa

from retrosheetpy.schemas.parks import PARK_SCHEMA, parse_park_line


class ParkParser:
    """Parses Retrosheet parkcode.txt into a strongly-typed PyArrow Table."""

    def parse_file(self, path: Path) -> pa.Table:
        """Parses parkcode.txt into an Arrow Table conforming to PARK_SCHEMA."""
        records: list[dict[str, object]] = []
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parsed = parse_park_line(line)
                if parsed is not None:
                    records.append(parsed)

        if not records:
            return pa.Table.from_batches([], schema=PARK_SCHEMA)

        arrays = []
        for field in PARK_SCHEMA:
            col_name = field.name
            col_type = field.type
            col_vals = [r.get(col_name) for r in records]
            arrays.append(pa.array(col_vals, type=col_type))

        return pa.Table.from_arrays(arrays, schema=PARK_SCHEMA)

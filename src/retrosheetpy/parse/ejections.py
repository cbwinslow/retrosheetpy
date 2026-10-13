"""Parser for Retrosheet Official Ejections Log (ejections.csv)."""

from __future__ import annotations

import csv
from pathlib import Path

import pyarrow as pa

from retrosheetpy.schemas.ejections import EJECTION_SCHEMA
from retrosheetpy.schemas.types import parse_date, parse_int


class EjectionParser:
    """Parses Retrosheet ejections.csv into a strongly-typed PyArrow Table."""

    def parse_file(self, path: Path) -> pa.Table:
        """Parses ejections.csv into an Arrow Table conforming to EJECTION_SCHEMA."""
        records: list[dict[str, object]] = []

        with path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = None
            for row in reader:
                if not row:
                    continue
                if header is None:
                    header = [c.strip().lower() for c in row]
                    continue

                row_dict = dict(zip(header, row, strict=False))
                records.append(
                    {
                        "game_id": row_dict.get("gameid") or None,
                        "date": parse_date(row_dict.get("date")),
                        "dh": row_dict.get("dh") or None,
                        "ejectee_id": row_dict.get("ejectee") or "",
                        "ejectee_name": row_dict.get("ejecteename") or None,
                        "team_id": row_dict.get("team") or None,
                        "job": row_dict.get("job") or None,
                        "umpire_id": row_dict.get("umpire") or None,
                        "umpire_name": row_dict.get("umpirename") or None,
                        "inning": parse_int(row_dict.get("inning")),
                        "reason": row_dict.get("reason") or None,
                    }
                )

        if not records:
            return pa.Table.from_batches([], schema=EJECTION_SCHEMA)

        arrays = []
        for field in EJECTION_SCHEMA:
            col_vals = [r.get(field.name) for r in records]
            arrays.append(pa.array(col_vals, type=field.type))

        return pa.Table.from_arrays(arrays, schema=EJECTION_SCHEMA)

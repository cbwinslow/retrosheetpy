"""Parser for Retrosheet Schedules (YYYYschedule.csv / YYYYsked.txt)."""

from __future__ import annotations

import csv
from pathlib import Path

import pyarrow as pa

from retrosheetpy.schemas.schedules import SCHEDULE_SCHEMA
from retrosheetpy.schemas.types import parse_date, parse_int


class ScheduleParser:
    """Parses Retrosheet schedule files into a strongly-typed PyArrow Table."""

    def parse_file(self, path: Path) -> pa.Table:
        """Parses a schedule file into an Arrow Table conforming to SCHEDULE_SCHEMA."""
        records: list[dict[str, object]] = []

        with path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                # Skip header row if present
                if row[0].strip().lower() in ("date", '"date"'):
                    continue
                if len(row) < 10:
                    continue

                date_val = parse_date(row[0])
                game_num_val = parse_int(row[1])
                day_val = row[2].strip() if len(row) > 2 else None
                vis_team = row[3].strip() if len(row) > 3 else None
                vis_lg = row[4].strip() if len(row) > 4 else None
                vis_num = parse_int(row[5]) if len(row) > 5 else None
                home_team = row[6].strip() if len(row) > 6 else None
                home_lg = row[7].strip() if len(row) > 7 else None
                home_num = parse_int(row[8]) if len(row) > 8 else None
                dn = row[9].strip() if len(row) > 9 else None

                # Optional columns depending on year: park_id/location, postponed, makeup
                park_id = None
                postponed = None
                makeup_date = None

                if len(row) == 12:
                    # 1990 format: postponed at index 10, makeup at index 11
                    postponed = row[10].strip() or None
                    makeup_date = parse_date(row[11])
                elif len(row) >= 13:
                    # 2024 format: location at index 10, postponed at 11, makeup at 12
                    park_id = row[10].strip() or None
                    postponed = row[11].strip() or None
                    makeup_date = parse_date(row[12])
                elif len(row) == 11:
                    park_id = row[10].strip() or None

                records.append(
                    {
                        "date": date_val,
                        "game_num": game_num_val,
                        "day_of_week": day_val,
                        "vis_team": vis_team,
                        "vis_league": vis_lg,
                        "vis_game_num": vis_num,
                        "home_team": home_team,
                        "home_league": home_lg,
                        "home_game_num": home_num,
                        "day_night": dn,
                        "park_id": park_id,
                        "postponed": postponed,
                        "makeup_date": makeup_date,
                    }
                )

        if not records:
            return pa.Table.from_batches([], schema=SCHEDULE_SCHEMA)

        arrays = []
        for field in SCHEDULE_SCHEMA:
            col_vals = [r.get(field.name) for r in records]
            arrays.append(pa.array(col_vals, type=field.type))

        return pa.Table.from_arrays(arrays, schema=SCHEDULE_SCHEMA)

    def parse_files(self, paths: list[Path]) -> pa.Table:
        """Parses multiple schedule files and concatenates into a single Arrow Table."""
        tables = [self.parse_file(p) for p in paths]
        valid = [t for t in tables if t.num_rows > 0]
        if not valid:
            return pa.Table.from_batches([], schema=SCHEDULE_SCHEMA)
        return pa.concat_tables(valid)

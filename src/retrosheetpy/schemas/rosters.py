"""Strongly-typed PyArrow schema and parser for Retrosheet Rosters (.ROS)."""

from __future__ import annotations

import csv
import io
from typing import Any

import pyarrow as pa

from retrosheetpy.schemas.types import parse_int

ROSTER_SCHEMA: pa.Schema = pa.schema(
    [
        ("year", pa.int16()),
        ("team_id", pa.string()),
        ("player_id", pa.string()),
        ("last_name", pa.string()),
        ("first_name", pa.string()),
        ("bats", pa.string()),
        ("throws", pa.string()),
        ("position", pa.string()),
    ]
)


def parse_roster_line(
    line: str, year: int | None = None, team_id: str | None = None
) -> dict[str, Any]:
    """Parses a single roster line (player_id,last_name,first_name,bats,throws,team,position)."""
    reader = csv.reader(io.StringIO(line))
    parts = next(reader)
    # parts: [player_id, last_name, first_name, bats, throws, team, position]
    player_id = parts[0].strip() if len(parts) > 0 else ""
    last_name = parts[1].strip() if len(parts) > 1 else ""
    first_name = parts[2].strip() if len(parts) > 2 else ""
    bats = parts[3].strip() if len(parts) > 3 else ""
    throws = parts[4].strip() if len(parts) > 4 else ""
    t_id = parts[5].strip() if len(parts) > 5 and parts[5].strip() else (team_id or "")
    position = parts[6].strip() if len(parts) > 6 else ""

    return {
        "year": parse_int(year),
        "team_id": t_id,
        "player_id": player_id,
        "last_name": last_name,
        "first_name": first_name,
        "bats": bats,
        "throws": throws,
        "position": position,
    }

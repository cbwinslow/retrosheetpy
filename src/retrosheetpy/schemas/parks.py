"""Strongly-typed PyArrow schema and parser for Retrosheet Ballparks (parkcode.txt)."""

from __future__ import annotations

import csv
import io
from typing import Any

import pyarrow as pa

from retrosheetpy.schemas.types import parse_date

PARK_SCHEMA: pa.Schema = pa.schema(
    [
        ("park_id", pa.string()),
        ("name", pa.string()),
        ("aka", pa.string()),
        ("city", pa.string()),
        ("state", pa.string()),
        ("start_date", pa.date32()),
        ("end_date", pa.date32()),
        ("league", pa.string()),
        ("notes", pa.string()),
    ]
)


def parse_park_line(line: str) -> dict[str, Any] | None:
    """Parses a single parkcode line (PARKID,NAME,AKA,CITY,STATE,START,END,LEAGUE,NOTES)."""
    s = line.strip()
    if not s or s.startswith("PARKID"):
        return None
    reader = csv.reader(io.StringIO(s))
    parts = next(reader)
    if not parts or not parts[0]:
        return None

    return {
        "park_id": parts[0].strip(),
        "name": parts[1].strip() if len(parts) > 1 else "",
        "aka": parts[2].strip() if len(parts) > 2 else "",
        "city": parts[3].strip() if len(parts) > 3 else "",
        "state": parts[4].strip() if len(parts) > 4 else "",
        "start_date": parse_date(parts[5]) if len(parts) > 5 else None,
        "end_date": parse_date(parts[6]) if len(parts) > 6 else None,
        "league": parts[7].strip() if len(parts) > 7 else "",
        "notes": parts[8].strip() if len(parts) > 8 else "",
    }

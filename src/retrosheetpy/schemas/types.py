"""Type coercion helpers for converting raw Retrosheet strings into strongly typed values."""

from __future__ import annotations

import datetime
from typing import Any


def parse_date(val: Any) -> datetime.date | None:
    """Parses YYYYMMDD or MM/DD/YYYY string into datetime.date."""
    if not val:
        return None
    s = str(val).strip()
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            try:
                # MM/DD/YYYY
                return datetime.date(int(parts[2]), int(parts[0]), int(parts[1]))
            except ValueError:
                return None
    clean = s.replace("-", "").replace("/", "")
    if len(clean) == 8 and clean.isdigit():
        try:
            return datetime.date(int(clean[:4]), int(clean[4:6]), int(clean[6:8]))
        except ValueError:
            return None
    return None


def parse_int(val: Any, default: int | None = None) -> int | None:
    """Safely converts string/number into integer or None."""
    if val is None:
        return default
    s = str(val).strip()
    if not s:
        return default
    try:
        return int(s)
    except ValueError:
        return default


def parse_float(val: Any, default: float | None = None) -> float | None:
    """Safely converts string/number into float or None."""
    if val is None:
        return default
    s = str(val).strip()
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def parse_bool(val: Any) -> bool | None:
    """Safely converts Retrosheet 'T'/'F'/'1'/'0' flag into boolean."""
    if val is None:
        return None
    s = str(val).strip().upper()
    if s in ("T", "TRUE", "1", "Y", "YES"):
        return True
    if s in ("F", "FALSE", "0", "N", "NO"):
        return False
    return None

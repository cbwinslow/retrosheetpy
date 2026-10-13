"""Strongly-typed PyArrow schema and parser for Retrosheet Game Logs (glYYYY.txt)."""

from __future__ import annotations

import csv
import io
from typing import Any

import pyarrow as pa

from retrosheetpy.schemas.types import parse_date, parse_int

_GAMELOG_COLUMN_SPECS: list[tuple[str, pa.DataType]] = [
    ("date", pa.date32()),
    ("game_number", pa.int8()),
    ("day_of_week", pa.string()),
    ("visiting_team", pa.string()),
    ("visiting_league", pa.string()),
    ("visiting_game_num", pa.int16()),
    ("home_team", pa.string()),
    ("home_league", pa.string()),
    ("home_game_num", pa.int16()),
    ("visiting_score", pa.int16()),
    ("home_score", pa.int16()),
    ("length_outs", pa.int16()),
    ("day_night", pa.string()),
    ("completion_info", pa.string()),
    ("forfeit_info", pa.string()),
    ("protest_info", pa.string()),
    ("park_id", pa.string()),
    ("attendance", pa.int32()),
    ("time_minutes", pa.int16()),
    ("visiting_line_score", pa.string()),
    ("home_line_score", pa.string()),
    # Visiting offensive stats
    ("visiting_ab", pa.int16()),
    ("visiting_hits", pa.int16()),
    ("visiting_2b", pa.int16()),
    ("visiting_3b", pa.int16()),
    ("visiting_hr", pa.int16()),
    ("visiting_rbi", pa.int16()),
    ("visiting_sh", pa.int16()),
    ("visiting_sf", pa.int16()),
    ("visiting_hbp", pa.int16()),
    ("visiting_bb", pa.int16()),
    ("visiting_ibb", pa.int16()),
    ("visiting_so", pa.int16()),
    ("visiting_sb", pa.int16()),
    ("visiting_cs", pa.int16()),
    ("visiting_gidp", pa.int16()),
    ("visiting_ci", pa.int16()),
    ("visiting_lob", pa.int16()),
    ("visiting_pitchers_used", pa.int16()),
    ("visiting_ind_er", pa.int16()),
    ("visiting_team_er", pa.int16()),
    ("visiting_wild_pitches", pa.int16()),
    ("visiting_balks", pa.int16()),
    # Visiting defensive stats
    ("visiting_putouts", pa.int16()),
    ("visiting_assists", pa.int16()),
    ("visiting_errors", pa.int16()),
    ("visiting_passed_balls", pa.int16()),
    ("visiting_dp", pa.int16()),
    ("visiting_tp", pa.int16()),
    # Home offensive stats
    ("home_ab", pa.int16()),
    ("home_hits", pa.int16()),
    ("home_2b", pa.int16()),
    ("home_3b", pa.int16()),
    ("home_hr", pa.int16()),
    ("home_rbi", pa.int16()),
    ("home_sh", pa.int16()),
    ("home_sf", pa.int16()),
    ("home_hbp", pa.int16()),
    ("home_bb", pa.int16()),
    ("home_ibb", pa.int16()),
    ("home_so", pa.int16()),
    ("home_sb", pa.int16()),
    ("home_cs", pa.int16()),
    ("home_gidp", pa.int16()),
    ("home_ci", pa.int16()),
    ("home_lob", pa.int16()),
    # Home pitching & defensive stats
    ("home_pitchers_used", pa.int16()),
    ("home_ind_er", pa.int16()),
    ("home_team_er", pa.int16()),
    ("home_wild_pitches", pa.int16()),
    ("home_balks", pa.int16()),
    ("home_putouts", pa.int16()),
    ("home_assists", pa.int16()),
    ("home_errors", pa.int16()),
    ("home_passed_balls", pa.int16()),
    ("home_dp", pa.int16()),
    ("home_tp", pa.int16()),
    # Umpires
    ("hp_ump_id", pa.string()),
    ("hp_ump_name", pa.string()),
    ("1b_ump_id", pa.string()),
    ("1b_ump_name", pa.string()),
    ("2b_ump_id", pa.string()),
    ("2b_ump_name", pa.string()),
    ("3b_ump_id", pa.string()),
    ("3b_ump_name", pa.string()),
    ("lf_ump_id", pa.string()),
    ("lf_ump_name", pa.string()),
    ("rf_ump_id", pa.string()),
    ("rf_ump_name", pa.string()),
    # Managers
    ("visiting_mgr_id", pa.string()),
    ("visiting_mgr_name", pa.string()),
    ("home_mgr_id", pa.string()),
    ("home_mgr_name", pa.string()),
    # Pitchers of record / Game-winning RBI
    ("winning_pitcher_id", pa.string()),
    ("winning_pitcher_name", pa.string()),
    ("losing_pitcher_id", pa.string()),
    ("losing_pitcher_name", pa.string()),
    ("save_pitcher_id", pa.string()),
    ("save_pitcher_name", pa.string()),
    ("gwrbi_id", pa.string()),
    ("gwrbi_name", pa.string()),
    ("visiting_starting_pitcher_id", pa.string()),
    ("visiting_starting_pitcher_name", pa.string()),
    ("home_starting_pitcher_id", pa.string()),
    ("home_starting_pitcher_name", pa.string()),
]

# Generate Visiting Lineup (9 batters * 3 fields = 27 fields)
for idx in range(1, 10):
    _GAMELOG_COLUMN_SPECS.extend(
        [
            (f"visiting_batter_{idx}_id", pa.string()),
            (f"visiting_batter_{idx}_name", pa.string()),
            (f"visiting_batter_{idx}_pos", pa.int8()),
        ]
    )

# Generate Home Lineup (9 batters * 3 fields = 27 fields)
for idx in range(1, 10):
    _GAMELOG_COLUMN_SPECS.extend(
        [
            (f"home_batter_{idx}_id", pa.string()),
            (f"home_batter_{idx}_name", pa.string()),
            (f"home_batter_{idx}_pos", pa.int8()),
        ]
    )

_GAMELOG_COLUMN_SPECS.extend(
    [
        ("additional_info", pa.string()),
        ("acquisition_info", pa.string()),
    ]
)

GAMELOG_SCHEMA: pa.Schema = pa.schema(_GAMELOG_COLUMN_SPECS)
_COLUMN_NAMES: list[str] = [name for name, _ in _GAMELOG_COLUMN_SPECS]
_COLUMN_TYPES: list[pa.DataType] = [dtype for _, dtype in _GAMELOG_COLUMN_SPECS]


def parse_gamelog_line(line: str) -> dict[str, Any]:
    """Parses a single comma-delimited game log line into a typed dictionary."""
    reader = csv.reader(io.StringIO(line))
    raw_vals = next(reader)
    row: dict[str, Any] = {}

    for i, col_name in enumerate(_COLUMN_NAMES):
        if i >= len(raw_vals):
            row[col_name] = None
            continue
        val = raw_vals[i].strip()
        expected_type = _COLUMN_TYPES[i]

        if not val:
            row[col_name] = None
        elif expected_type == pa.date32():
            row[col_name] = parse_date(val)
        elif pa.types.is_integer(expected_type):
            row[col_name] = parse_int(val)
        else:
            row[col_name] = val

    return row

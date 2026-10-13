"""SQL DDL generator for Retrosheet schemas across PostgreSQL, DuckDB, and SQLite dialects."""

from __future__ import annotations

import pyarrow as pa

from retrosheetpy.schemas.events import EVENT_SCHEMA
from retrosheetpy.schemas.gamelogs import GAMELOG_SCHEMA
from retrosheetpy.schemas.parks import PARK_SCHEMA
from retrosheetpy.schemas.rosters import ROSTER_SCHEMA

_SCHEMAS: dict[str, tuple[str, pa.Schema]] = {
    "events": ("events", EVENT_SCHEMA),
    "gamelogs": ("game_logs", GAMELOG_SCHEMA),
    "game_logs": ("game_logs", GAMELOG_SCHEMA),
    "rosters": ("rosters", ROSTER_SCHEMA),
    "parks": ("parks", PARK_SCHEMA),
}


def _arrow_to_sql_type(dtype: pa.DataType, dialect: str) -> str:
    d = dialect.lower()

    if dtype == pa.date32():
        return "TEXT" if d == "sqlite" else "DATE"

    if dtype == pa.bool_():
        return "INTEGER" if d == "sqlite" else "BOOLEAN"

    if dtype == pa.int8():
        if d == "duckdb":
            return "TINYINT"
        elif d == "sqlite":
            return "INTEGER"
        return "SMALLINT"

    if dtype == pa.int16():
        return "INTEGER" if d == "sqlite" else "SMALLINT"

    if dtype == pa.int32():
        return "INTEGER"

    if dtype == pa.string():
        return "TEXT" if d == "sqlite" else "VARCHAR"

    return "TEXT" if d == "sqlite" else "VARCHAR"


def generate_ddl(dataset: str, dialect: str = "postgres") -> str:
    """Generates standard SQL DDL CREATE TABLE statement for a given Retrosheet dataset."""
    key = dataset.lower()
    if key not in _SCHEMAS:
        raise ValueError(f"Unknown dataset '{dataset}'. Choose from: {list(_SCHEMAS.keys())}")

    table_name, schema = _SCHEMAS[key]
    lines: list[str] = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]

    cols: list[str] = []
    for field in schema:
        sql_type = _arrow_to_sql_type(field.type, dialect)
        cols.append(f"    {field.name} {sql_type}")

    lines.append(",\n".join(cols))
    lines.append(");")
    return "\n".join(lines)

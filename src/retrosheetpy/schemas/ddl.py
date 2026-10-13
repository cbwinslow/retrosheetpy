"""SQL DDL generator for Retrosheet schemas across PostgreSQL, DuckDB, SQLite, Snowflake, and BigQuery dialects."""

from __future__ import annotations

import pyarrow as pa

from retrosheetpy.schemas.bio import BIO_SCHEMA
from retrosheetpy.schemas.ejections import EJECTION_SCHEMA
from retrosheetpy.schemas.events import EVENT_SCHEMA
from retrosheetpy.schemas.gamelogs import GAMELOG_SCHEMA
from retrosheetpy.schemas.parks import PARK_SCHEMA
from retrosheetpy.schemas.rosters import ROSTER_SCHEMA
from retrosheetpy.schemas.schedules import SCHEDULE_SCHEMA
from retrosheetpy.schemas.transactions import TRANSACTION_SCHEMA

_SCHEMAS: dict[str, tuple[str, pa.Schema]] = {
    "events": ("events", EVENT_SCHEMA),
    "postseason": ("postseason_events", EVENT_SCHEMA),
    "allstar": ("allstar_events", EVENT_SCHEMA),
    "gamelogs": ("game_logs", GAMELOG_SCHEMA),
    "game_logs": ("game_logs", GAMELOG_SCHEMA),
    "rosters": ("rosters", ROSTER_SCHEMA),
    "parks": ("parks", PARK_SCHEMA),
    "schedules": ("schedules", SCHEDULE_SCHEMA),
    "bio": ("biographical", BIO_SCHEMA),
    "ejections": ("ejections", EJECTION_SCHEMA),
    "transactions": ("transactions", TRANSACTION_SCHEMA),
}


def _arrow_to_sql_type(dtype: pa.DataType, dialect: str) -> str:
    d = dialect.lower()

    if dtype == pa.date32():
        if d == "sqlite":
            return "TEXT"
        return "DATE"

    if dtype == pa.bool_():
        if d == "sqlite":
            return "INTEGER"
        if d == "bigquery":
            return "BOOL"
        return "BOOLEAN"

    if dtype == pa.int8():
        if d == "duckdb":
            return "TINYINT"
        if d in ("sqlite", "bigquery"):
            return "INTEGER" if d == "sqlite" else "INT64"
        return "SMALLINT"

    if dtype == pa.int16():
        if d == "sqlite":
            return "INTEGER"
        if d == "bigquery":
            return "INT64"
        return "SMALLINT"

    if dtype == pa.int32():
        if d == "bigquery":
            return "INT64"
        return "INTEGER"

    if dtype == pa.string():
        if d == "sqlite":
            return "TEXT"
        if d == "bigquery":
            return "STRING"
        return "VARCHAR"

    if d == "bigquery":
        return "STRING"
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

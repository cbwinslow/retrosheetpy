from pathlib import Path

import duckdb
import pyarrow as pa
import pytest

from retrosheetpy.schemas.ddl import generate_ddl
from retrosheetpy.sink.duckdb_sink import DuckDBSink


def test_generate_ddl_dialects() -> None:
    # Postgres
    pg_events = generate_ddl("events", dialect="postgres")
    assert "CREATE TABLE IF NOT EXISTS events (" in pg_events
    assert "GAME_ID VARCHAR" in pg_events
    assert "INN_CT SMALLINT" in pg_events
    assert "LEADOFF_FL BOOLEAN" in pg_events

    # DuckDB
    duck_gl = generate_ddl("gamelogs", dialect="duckdb")
    assert "CREATE TABLE IF NOT EXISTS game_logs (" in duck_gl
    assert "date DATE" in duck_gl
    assert "attendance INTEGER" in duck_gl
    assert "game_number TINYINT" in duck_gl

    # SQLite
    sqlite_parks = generate_ddl("parks", dialect="sqlite")
    assert "CREATE TABLE IF NOT EXISTS parks (" in sqlite_parks
    assert "start_date TEXT" in sqlite_parks


def test_pre_existing_table_column_alignment(tmp_path: Path) -> None:
    db_path = tmp_path / "pre_existing.duckdb"
    con = duckdb.connect(str(db_path))

    # Pre-create table with columns in a DIFFERENT order and an extra column with DEFAULT
    con.execute("""
        CREATE TABLE rosters (
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            player_id VARCHAR,
            year SMALLINT,
            last_name VARCHAR
        );
    """)
    con.close()

    # Create Arrow data with extra columns not in the destination table
    table = pa.Table.from_pydict(
        {
            "player_id": ["judge001", "soot001"],
            "year": [2024, 2024],
            "last_name": ["Judge", "Soto"],
            "bats": ["R", "L"],  # not in destination table
            "position": ["OF", "OF"],  # not in destination table
        }
    )

    sink = DuckDBSink(db_path=db_path)
    # Append into pre-existing table
    sink.write_table("rosters", table)
    sink.close()

    # Query back and verify that columns aligned properly and created_at was populated
    con2 = duckdb.connect(str(db_path))
    rows = con2.execute(
        "SELECT player_id, year, last_name, created_at IS NOT NULL FROM rosters ORDER BY last_name"
    ).fetchall()
    assert rows == [
        ("judge001", 2024, "Judge", True),
        ("soot001", 2024, "Soto", True),
    ]
    con2.close()


def test_pre_existing_table_no_matching_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "mismatch.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute("CREATE TABLE foo (bar INTEGER);")
    con.close()

    table = pa.Table.from_pydict({"alpha": ["x", "y"]})
    sink = DuckDBSink(db_path=db_path)
    with pytest.raises(ValueError, match="No matching columns found"):
        sink.write_table("foo", table)
    sink.close()

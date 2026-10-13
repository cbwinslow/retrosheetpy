"""DuckDB destination sink for storing strongly-typed Retrosheet tables."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pyarrow as pa


class DuckDBSink:
    """Manages writing strongly-typed PyArrow Tables into an embedded DuckDB database."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(self.db_path)

    def write_table(self, table_name: str, table: pa.Table, mode: str = "append") -> None:
        """Writes or appends an Arrow Table to a DuckDB table."""
        if table.num_rows == 0:
            return

        # Register arrow table in DuckDB session
        self.con.register("_incoming_arrow", table)

        # Check if table already exists
        exists = self.con.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name],
        ).fetchone()

        table_exists = exists is not None and exists[0] > 0

        if not table_exists or mode == "replace":
            if mode == "replace" and table_exists:
                self.con.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM _incoming_arrow")
        else:
            # Query columns in destination table
            dest_col_rows = self.con.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
                [table_name],
            ).fetchall()
            dest_cols = [r[0] for r in dest_col_rows]
            matching_cols = [c for c in dest_cols if c in table.column_names]

            if not matching_cols:
                raise ValueError(
                    f"No matching columns found between incoming data and existing table '{table_name}'."
                )

            cols_sql = ", ".join(f'"{c}"' for c in matching_cols)
            self.con.execute(
                f"INSERT INTO {table_name} ({cols_sql}) SELECT {cols_sql} FROM _incoming_arrow"
            )

        self.con.unregister("_incoming_arrow")

    def execute(self, sql: str, params: list[object] | None = None) -> duckdb.DuckDBPyConnection:
        """Executes arbitrary SQL queries on the DuckDB database."""
        return self.con.execute(sql, params or [])

    def close(self) -> None:
        """Closes the DuckDB connection."""
        self.con.close()

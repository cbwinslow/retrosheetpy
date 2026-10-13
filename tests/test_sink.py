from pathlib import Path

import duckdb
import pyarrow as pa

from retrosheetpy.schemas.rosters import ROSTER_SCHEMA
from retrosheetpy.sink.dataframe import to_arrow, to_pandas, to_polars
from retrosheetpy.sink.duckdb_sink import DuckDBSink
from retrosheetpy.sink.file_sink import FileSink


def _sample_table() -> pa.Table:
    data = [
        {
            "year": 2024,
            "team_id": "NYA",
            "player_id": "judge001",
            "last_name": "Judge",
            "first_name": "Aaron",
            "bats": "R",
            "throws": "R",
            "position": "OF",
        },
        {
            "year": 2024,
            "team_id": "NYA",
            "player_id": "soot001",
            "last_name": "Soto",
            "first_name": "Juan",
            "bats": "L",
            "throws": "R",
            "position": "OF",
        },
    ]
    arrays = []
    for f in ROSTER_SCHEMA:
        arrays.append(pa.array([d[f.name] for d in data], type=f.type))
    return pa.Table.from_arrays(arrays, schema=ROSTER_SCHEMA)


def test_duckdb_sink(tmp_path: Path) -> None:
    db_path = tmp_path / "baseball.duckdb"
    sink = DuckDBSink(db_path=db_path)
    table = _sample_table()

    sink.write_table("rosters", table)
    sink.close()

    # Query back using raw duckdb to verify typed schema
    con = duckdb.connect(str(db_path))
    res = con.execute(
        "SELECT player_id, last_name, year FROM rosters ORDER BY last_name"
    ).fetchall()
    assert res == [("judge001", "Judge", 2024), ("soot001", "Soto", 2024)]

    # Verify column types in DuckDB
    col_rows = con.execute("DESCRIBE rosters").fetchall()
    col_info = {r[0]: r[1] for r in col_rows}
    assert "INT" in col_info["year"] or "SHORT" in col_info["year"]
    con.close()


def test_parquet_sink(tmp_path: Path) -> None:
    out_file = tmp_path / "rosters.parquet"
    sink = FileSink()
    table = _sample_table()

    sink.write_parquet(out_file, table)
    assert out_file.exists()

    # Verify reading parquet
    con = duckdb.connect()
    res = con.execute(f"SELECT count(*) FROM '{out_file}'").fetchone()
    assert res is not None and res[0] == 2
    con.close()


def test_dataframe_converters() -> None:
    table = _sample_table()

    # Arrow
    arrow_tbl = to_arrow(table)
    assert isinstance(arrow_tbl, pa.Table)
    assert arrow_tbl.num_rows == 2

    # Polars (if installed)
    try:
        import polars as pl

        df_pl = to_polars(table)
        assert isinstance(df_pl, pl.DataFrame)
        assert df_pl.shape == (2, 8)
    except ImportError:
        pass

    # pandas (if installed)
    try:
        import pandas as pd

        df_pd = to_pandas(table)
        assert isinstance(df_pd, pd.DataFrame)
        assert len(df_pd) == 2
    except ImportError:
        pass

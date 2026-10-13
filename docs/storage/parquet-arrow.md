# Parquet & PyArrow

Columnar storage formats like **Apache Parquet** provide 10x–20x disk compression and fast read performance compared to raw CSV files.

`retrosheetpy` uses [PyArrow](https://arrow.apache.org/docs/python/) internally as its core data exchange format, allowing direct export to Parquet and CSV without serialization overhead.

---

## Writing Parquet Files (`to_parquet`)

```python
import retrosheetpy as rs

# Export 2024 game logs to a compressed Parquet file
rs.to_parquet(
    path="gamelogs_2024.parquet",
    dataset="gamelogs",
    years=[2024],
    compression="snappy",  # "snappy", "zstd", "gzip", "none"
)
```

Exporting multi-year datasets:

```python
# Export 25 years of game logs (1990-2024) into a single Parquet file (~12 MB)
rs.to_parquet(
    path="gamelogs_1990_2024.parquet",
    dataset="gamelogs",
    years=range(1990, 2025),
    compression="zstd",
)
```

---

## Reading Back in Polars & pandas

Because the Parquet file contains embedded Arrow schema metadata, types (dates, integers, booleans) are preserved exactly without manual casting:

=== "Polars"
    ```python
    import polars as pl

    df = pl.read_parquet("gamelogs_1990_2024.parquet")
    print(df.schema)
    ```

=== "pandas"
    ```python
    import pandas as pd

    df = pd.read_parquet("gamelogs_1990_2024.parquet")
    print(df.dtypes)
    ```

=== "DuckDB"
    ```python
    import duckdb

    # Query the Parquet file directly with zero import time!
    duckdb.sql("SELECT COUNT(*) FROM 'gamelogs_1990_2024.parquet'")
    ```

---

## Direct In-Memory PyArrow Tables

If you are building custom streaming pipelines or distributed Ray / Dask jobs, you can obtain native `pyarrow.Table` objects directly:

```python
import retrosheetpy as rs

table = rs.events(year=2024, backend="arrow")

print(f"Num rows: {table.num_rows:,}")
print(f"Schema columns: {len(table.schema)}")
```

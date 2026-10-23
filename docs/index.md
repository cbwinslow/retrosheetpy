# retrosheetpy

<p align="center">
  <b>Fast, strongly-typed Retrosheet baseball data downloader, parser, and database ingestor.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/retrosheetpy/"><img src="https://img.shields.io/pypi/v/retrosheetpy.svg?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/retrosheetpy/"><img src="https://img.shields.io/pypi/pyversions/retrosheetpy.svg" alt="Python Versions"></a>
  <a href="https://github.com/cbwinslow/retrosheetpy/actions/workflows/ci.yml"><img src="https://github.com/cbwinslow/retrosheetpy/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/cbwinslow/retrosheetpy/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--or--later-green.svg" alt="License"></a>
</p>

---

`retrosheetpy` brings modern data workflows to [Retrosheet](https://www.retrosheet.org) baseball archives. It enables baseball researchers, analysts, professors, and DBAs to download, parse, and ingest play-by-play events, historical game logs, rosters, and ballparks directly into **DuckDB, Parquet, Polars, pandas, and SQL databases** with **strongly-typed schemas** (integers, dates, booleans—never raw text dumps).

Downloads default to the fast, rate-limit-free GitHub Fastly raw CDN mirror (`chadwickbureau/retrosheet`) with automatic fallback to `retrosheet.org`. Powered by [`chadwickpy`](https://github.com/cbwinslow/chadwickpy) for multi-core play-by-play parsing with **zero C compiler dependencies**.

---

## Unified Ingestion & Querying

One API to download, parse, and stream baseball data into your favorite analytical stack:

=== "DuckDB"
    ```python
    import retrosheetpy as rs

    # Ingest 2020 through 2024 into a local embedded analytical database
    rs.to_duckdb(
        path="baseball.duckdb",
        years=range(2020, 2025),
        datasets=["events", "gamelogs", "rosters", "parks"],
    )
    ```

=== "Polars DataFrame"
    ```python
    import retrosheetpy as rs

    # Blazing-fast play-by-play events in Polars
    events_2024 = rs.events(year=2024, backend="polars")
    print(events_2024.select(["GAME_ID", "BAT_ID", "PIT_ID", "EVENT_TX"]))
    ```

=== "pandas DataFrame"
    ```python
    import retrosheetpy as rs

    # 1871-present historical game logs
    gl = rs.game_logs(year=2024, backend="pandas")
    print(gl[["date", "visiting_team", "visiting_score", "home_team", "home_score"]].head())
    ```

=== "Parquet / PyArrow"
    ```python
    import retrosheetpy as rs

    # Export compressed columnar Parquet files
    rs.to_parquet("gamelogs_1990_2024.parquet", dataset="gamelogs", years=range(1990, 2025))
    ```

=== "PostgreSQL & dlt"
    ```python
    import retrosheetpy as rs

    # Stream multi-season datasets directly into PostgreSQL or Snowflake
    rs.to_dlt(
        destination="postgres://postgres:postgres@localhost:5432/retrosheet",
        years=[2023, 2024],
        datasets=["rosters", "parks", "gamelogs"],
        dataset_name="public",
    )
    ```

=== "SQL DDL"
    ```python
    import retrosheetpy as rs

    # Generate typed CREATE TABLE DDL for any dataset and database dialect
    print(rs.get_ddl("events", dialect="postgres"))
    print(rs.get_ddl("gamelogs", dialect="duckdb"))
    ```

---

## Why retrosheetpy?

```mermaid
flowchart LR
    A["Retrosheet.org\n(HTTP Archives)"] --> B["Smart Cache\n(~/.cache/retrosheetpy)"]
    B --> C["Typed Parsers\n(chadwickpy + Arrow)"]
    C --> D1["DuckDB\n(Analytics)"]
    C --> D2["Parquet / Arrow\n(Data Lake)"]
    C --> D3["Polars / pandas\n(In-Memory)"]
    C --> D4["Postgres / Cloud\n(via dlt)"]
```

* **Zero C Compiler Required**: 100% pure Python / PyArrow wheels. Installable on Windows, macOS, and Linux in seconds with `pip` or `uv`.
* **Explicit, Strongly Typed Schemas**: Dates are parsed to `DATE`, counts and scores to `INTEGER`, flags to `BOOLEAN`. No untyped string conversions or silent failures.
* **Smart Bandwidth Caching**: Downloads once to `~/.cache/retrosheetpy/` with atomic writes, respecting Retrosheet server bandwidth.
* **Pre-Existing Table Alignment**: When ingesting into existing database tables, columns are automatically mapped by name—only matching columns are inserted.
* **Complete Retrosheet Catalog**: Regular season Events (play-by-play), Postseason, All-Star games, Game Logs (1871–present), Rosters, Ballparks, Schedules, Biographical encyclopedia, Ejections, and Player Transactions.

---

## The Retrosheet Notice

The information used in this project was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at [www.retrosheet.org](https://www.retrosheet.org).

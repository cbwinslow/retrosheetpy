# retrosheetpy

<p align="center"><b>Fast, strongly-typed Retrosheet baseball data downloader, parser, and database ingestor.</b></p>

<p align="center">
  <a href="https://pypi.org/project/retrosheetpy/"><img src="https://img.shields.io/pypi/v/retrosheetpy.svg?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/retrosheetpy/"><img src="https://img.shields.io/pypi/pyversions/retrosheetpy.svg" alt="Python Versions"></a>
  <a href="https://github.com/cbwinslow/retrosheetpy/actions/workflows/ci.yml"><img src="https://github.com/cbwinslow/retrosheetpy/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/cbwinslow/retrosheetpy/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--or--later-green.svg" alt="License"></a>
  <a href="https://cbwinslow.github.io/retrosheetpy/"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-informational.svg" alt="Documentation"></a>
</p>

---

`retrosheetpy` brings modern, typed data workflows to [Retrosheet](https://www.retrosheet.org) baseball archives. It enables baseball researchers, analysts, professors, and DBAs to download, parse, and ingest play-by-play events, historical game logs, rosters, schedules, and biographical encyclopedias directly into **DuckDB, Parquet, Polars, pandas, and cloud SQL warehouses** with **strongly-typed schemas** (integers, dates, booleans—never raw text dumps).

Powered by [`chadwickpy`](https://github.com/cbwinslow/chadwickpy) for multi-core play-by-play parsing with **zero C compiler dependencies**.

---

## Key Features

- **Zero C Compiler Required**: 100% pure Python / PyArrow / DuckDB, installable on Windows, macOS, and Linux in seconds.
- **Strongly Typed Schemas**: Dates are parsed to `DATE`, counts and scores to `INTEGER`, flags to `BOOLEAN`—ready for instant SQL queries without manual casting.
- **Complete Retrosheet Catalog**:
  - **Events** (Play-by-play, 164 columns via `chadwickpy`)
  - **Postseason & All-Star Games** (World Series, LCS, LDS, All-Star play-by-play)
  - **Game Logs** (1871–present, 161 columns)
  - **Official Schedules** (1877–present, 13 columns)
  - **Biographical Encyclopedia** (`biofile0.csv`, 32 columns)
  - **Team Rosters** (`.ROS` player records, handedness, teams)
  - **Ballparks** (`parkcode.txt`, history, dates, coordinates)
  - **Transactions & Ejections** (`tran.txt`, `ejections.csv`)
- **Compact CLI**: Compact flags (`-s`, `-y`, `-d`, `-c`, `-f`, `-o`) for downloading, ingesting, exporting, and generating DDL.
- **Cloud Warehouses via dlt**: Stream directly into PostgreSQL, Snowflake, BigQuery, ClickHouse, or Databricks via optional `dlt`.
- **LLM Context Ready**: Includes `llms.txt` and `llms-full.txt` conforming to the `llmstxt.org` specification for AI agents.

---

## Installation

```bash
# Core library (DuckDB, PyArrow, Polars, pandas, Parquet)
pip install retrosheetpy

# With cloud warehouse connectors (PostgreSQL, Snowflake, BigQuery)
pip install "retrosheetpy[dlt]"
```

---

## Quickstart

### Python API

```python
import retrosheetpy as rs

# 1. Download & inspect 2024 MLB play-by-play events
events = rs.events(year=2024, backend="polars")
print(events.select(["GAME_ID", "BAT_ID", "PIT_ID", "EVENT_TX"]))

# 2. Historical Game Logs (1871-present)
gamelogs = rs.game_logs(year=range(2020, 2025), backend="polars")

# 3. Ballpark Directory & Rosters
parks = rs.parks(backend="arrow")
rosters_2024 = rs.rosters(year=2024, backend="polars")

# 4. Schedules, Biofile, Ejections, Transactions
schedules = rs.schedules(year=2024, backend="polars")
bio = rs.bio(backend="polars")
ejections = rs.ejections(backend="polars")
transactions = rs.transactions(backend="polars")

# 5. Ingest decades directly into DuckDB
rs.to_duckdb(
    path="retrosheet.duckdb",
    years=range(2000, 2025),
    datasets=["events", "gamelogs", "rosters", "parks", "schedules", "bio"],
)

# 6. Stream into PostgreSQL via dlt
rs.to_dlt(
    destination="postgres",
    years=[2024],
    datasets=["events", "gamelogs", "rosters", "parks"],
    credentials="postgresql://user:pass@localhost:5432/retrosheet",
)
```

### Command-Line Interface (CLI)

```bash
# Download and cache all 2024 assets locally
retrosheetpy download -s all -y 2024

# Ingest into local DuckDB
retrosheetpy ingest -d duckdb -c retro.duckdb -s events,gamelogs -y 2020-2024

# Ingest into PostgreSQL warehouse
retrosheetpy ingest -d postgres -c "postgresql://user:pass@localhost:5432/retrosheet" -s all -y 2024

# Export specific dataset to Parquet
retrosheetpy export -s gamelogs -y 2024 -f parquet -o gamelogs_2024.parquet

# Generate production SQL DDL
retrosheetpy ddl -s events --dialect postgres
retrosheetpy ddl -s schedules --dialect bigquery
```

---

## Documentation & LLM Resources

- **Interactive Documentation**: [https://cbwinslow.github.io/retrosheetpy/](https://cbwinslow.github.io/retrosheetpy/)
- **LLM Summary Index**: [https://cbwinslow.github.io/retrosheetpy/llms.txt](https://cbwinslow.github.io/retrosheetpy/llms.txt)
- **Full LLM Context**: [https://cbwinslow.github.io/retrosheetpy/llms-full.txt](https://cbwinslow.github.io/retrosheetpy/llms-full.txt)
- **Robots.txt**: [https://cbwinslow.github.io/retrosheetpy/robots.txt](https://cbwinslow.github.io/retrosheetpy/robots.txt)
- **Sitemap**: [https://cbwinslow.github.io/retrosheetpy/sitemap.xml](https://cbwinslow.github.io/retrosheetpy/sitemap.xml)

---

## License & Attribution

`retrosheetpy` is licensed under GPL-3.0-or-later.

The information used in this project is obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at [www.retrosheet.org](https://www.retrosheet.org).

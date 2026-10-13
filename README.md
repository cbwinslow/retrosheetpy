# retrosheetpy

<p align="center"><b>Fast, strongly-typed Retrosheet baseball data downloader, parser, and database ingestor.</b></p>

`retrosheetpy` brings modern data workflows to [Retrosheet](https://www.retrosheet.org) baseball archives. It enables baseball researchers, analysts, professors, and DBAs to download, parse, and ingest play-by-play events, historical game logs, rosters, and biofiles directly into **DuckDB, Parquet, Polars, pandas, and SQL databases** with **strongly-typed schemas** (integers, dates, booleans—never raw text dumps).

Powered by [`chadwickpy`](https://github.com/cbwinslow/chadwickpy) for multi-core play-by-play parsing with **zero C compiler dependencies**.

---

## Key Features

- **No C Compiler Required**: 100% pure Python / PyArrow / DuckDB, installable on Windows, macOS, and Linux in seconds.
- **Strongly Typed Schemas**: Dates are parsed to `DATE`, counts and scores to `INTEGER`, flags to `BOOLEAN`—ready for instant SQL queries without manual casting.
- **Complete Retrosheet Catalog**:
  - **Events** (Play-by-play, via `chadwickpy`)
  - **Game Logs** (1871–present, 161+ columns)
  - **Rosters** (`.ROS` player records, handedness, teams)
  - **Ballparks** (`parks.csv`, history, dates, coordinates)
  - **Personnel Directory** (`biofile`, birth/death, debuts)
  - **Transactions & Ejections**
- **Smart Local Caching**: Download once to `~/.cache/retrosheetpy/` and reuse across workflows.
- **Decoupled Architecture**: Pluggable extractors, parsers, and sinks (Arrow, DuckDB, Parquet, CSV, and optional `dlt` for cloud data warehouses).

---

## Quickstart

```bash
pip install retrosheetpy
```

### Python API

```python
import retrosheetpy as rs

# 1. Download & inspect 2024 MLB play-by-play events
events = rs.events(year=2024)  # Returns Polars DataFrame by default
print(events.select(["GAME_ID", "BAT_ID", "PIT_ID", "EVENT_TX"]))

# 2. Historical Game Logs (1871-present)
gamelogs = rs.game_logs(years=[2023, 2024])

# 3. Ballpark Directory & Rosters
parks = rs.parks()
rosters_2024 = rs.rosters(year=2024)

# 4. Ingest decades directly into DuckDB
rs.to_duckdb(
    path="retrosheet.duckdb",
    years=range(2000, 2025),
    datasets=["events", "game_logs", "rosters", "parks"],
)
```

### Command-Line Interface (CLI)

```bash
# Ingest 2010 through 2024 into a local DuckDB database
retrosheetpy ingest --years 2010-2024 --dest duckdb --file retro.duckdb

# Export specific datasets to Parquet
retrosheetpy export --dataset game_logs --years 1980-2024 --format parquet --output-dir ./data/
```

---

## License & Attribution

`retrosheetpy` is licensed under GPL-3.0-or-later.

The information used in this project is obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at [www.retrosheet.org](https://www.retrosheet.org).

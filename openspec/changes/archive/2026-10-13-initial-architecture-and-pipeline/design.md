# Design: Initial Architecture & Ingestion Pipeline

## Architecture Overview
```text
┌────────────────────────────────────────────────────────┐
│                        User API                        │
│             import retrosheetpy as rs / CLI            │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Orchestration                       │
│            Workflow Pipeline & Cache Manager           │
└───────┬───────────────────┬────────────────────┬───────┘
        │                   │                    │
┌───────▼────────┐  ┌───────▼─────────┐  ┌───────▼───────┐
│ Extract Layer  │  │ Parse & Schemas │  │  Sink Layer   │
│ - Retrosheet   │  │ - chadwickpy    │  │ - DuckDB      │
│   HTTP Client  │  │   Event Bridge  │  │ - PyArrow     │
│ - Disk Cache   │  │ - GameLog Parser│  │ - Parquet     │
│ - Unzipper     │  │ - Roster Parser │  │ - Polars/df   │
│ - Manifest     │  │ - Bio/Park Parser│ │ - dlt (opt)   │
└────────────────┘  └─────────────────┘  └───────────────┘
```

## Stage Specifications

### 1. Extract (`src/retrosheetpy/extract/`)
- `manifest.py`: Authoritative URL mappings for Retrosheet assets:
  - Events: `https://www.retrosheet.org/events/{year}seve.zip`
  - Game Logs: `https://www.retrosheet.org/gamelogs/gl{year}.zip` (or decade zips)
  - Schedules: `https://www.retrosheet.org/schedule/{year}sked.zip`
  - Parks: `https://www.retrosheet.org/parkcode.txt`
  - Bio: `https://www.retrosheet.org/biofile.txt`
- `cache.py`: Default cache dir `~/.cache/retrosheetpy`. Tracks download timestamps, etags, and extracted directories.
- `downloader.py`: Async/sync `httpx` client with exponential backoff and progress bars.

### 2. Schemas & Types (`src/retrosheetpy/schemas/`)
- Explicit PyArrow schemas for:
  - `EVENT_SCHEMA`: 164 columns (dates as `date32()`, game counts as `int16()`, pitch sequences as `string()`, booleans as `bool_()`).
  - `GAMELOG_SCHEMA`: 161 columns (date, visiting/home team, scores as `int16()`, day/night, duration, attendance as `int32()`, pitcher/lineup IDs).
  - `ROSTER_SCHEMA`: Player ID, Last Name, First Name, Bats (`string`), Throws (`string`), Team, Pos.
  - `PARK_SCHEMA`: Park ID, Name, City, State, Start Date, End Date.
  - `BIO_SCHEMA`: Player ID, Birth Date, Death Date, Debut Date, etc.

### 3. Parse (`src/retrosheetpy/parse/`)
- `Protocol` definitions for each parser type.
- `events.py`: Feeds extracted event files to `chadwickpy.tools.events.event_rows` and yields Arrow batches using `EVENT_SCHEMA`.
- `gamelogs.py`: Parses fixed-order comma-delimited game log records with proper type casting.
- `rosters.py`: Parses `.ROS` files.

### 4. Sink (`src/retrosheetpy/sink/`)
- `duckdb.py`: Direct Arrow $\to$ DuckDB table loading (`duckdb.arrow(batch)` / `CREATE TABLE AS SELECT *`).
- `parquet.py`: Batched Parquet writer (`pyarrow.parquet.ParquetWriter`).
- `dataframe.py`: Conversions to Polars, Arrow Table, or pandas.
- `dlt_sink.py`: Optional integration exposing `@dlt.source` and `@dlt.resource`.

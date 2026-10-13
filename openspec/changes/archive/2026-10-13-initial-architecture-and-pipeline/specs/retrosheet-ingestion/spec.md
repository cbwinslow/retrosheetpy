# Capability: Retrosheet Ingestion

## ADDED Requirements

### Requirement: Download and Cache Retrosheet Archives
The system MUST download event files, game logs, schedules, and reference data from Retrosheet and store them in a local cache directory (`~/.cache/retrosheetpy/`) without re-downloading existing archives unless forced.

#### Scenario: First download of a season
- **GIVEN** the local cache does not contain `2024seve.zip`
- **WHEN** the user or pipeline requests 2024 event data
- **THEN** the client downloads `2024seve.zip` from retrosheet.org, verifies the archive, and extracts it to the cache.

#### Scenario: Repeated request uses cached data
- **GIVEN** `2024seve.zip` is already present and valid in the local cache
- **WHEN** the user requests 2024 event data without `--refresh`
- **THEN** no network request is made and the cached files are used directly.

### Requirement: Strongly-Typed Schema Enforcement
The system MUST parse Retrosheet records into strongly-typed PyArrow tables with explicit column types (dates as `date32`, counts and scores as `int16`/`int32`, flags as `bool_`, text as `string`), never loading all columns as raw text.

#### Scenario: Parsing event records
- **GIVEN** an extracted Retrosheet `.EVA` event file
- **WHEN** parsed through the Chadwick event bridge
- **THEN** the output PyArrow table has `GAME_DT` typed as `date32()`, `INN_CT` as `int16()`, `BAT_HOME_ID` as `int8()`, and `EVENT_TX` as `string()`.

#### Scenario: Parsing game logs
- **GIVEN** a Retrosheet game log file (`gl2024.txt`)
- **WHEN** parsed through the GameLog parser
- **THEN** scores, attendance, outs, and game durations are represented as numeric types and game dates as dates.

### Requirement: Multi-Destination Sinks
The system MUST provide decoupled sinks capable of outputting data into embedded DuckDB tables, Parquet files, and in-memory DataFrames (Polars, pandas, Arrow).

#### Scenario: Ingesting to DuckDB
- **GIVEN** parsed typed Arrow RecordBatches for season events
- **WHEN** ingested via `rs.to_duckdb(path, ...)`
- **THEN** DuckDB creates a strongly-typed `events` table and appends the records without runtime casting errors.

#### Scenario: Exporting to Parquet
- **GIVEN** parsed typed Arrow tables
- **WHEN** exported via `rs.to_parquet(path, ...)`
- **THEN** valid Snappy-compressed Parquet files are written preserving all schema metadata.

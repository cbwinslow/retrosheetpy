# retrosheet-ingestion Specification

## Purpose
Defines ingestion, schema parsing, and multi-sink export specifications for all Retrosheet baseball data.

## Requirements

### Requirement: Download and Cache Retrosheet Archives
The system MUST download event files, game logs, schedules, and reference data from configurable sources (defaulting to the GitHub raw CDN of the Chadwick Baseball Bureau mirror, with automatic fallback to retrosheet.org or custom mirror URLs) and store them in a local cache directory (`~/.cache/retrosheetpy/`) without re-downloading existing archives unless forced.

#### Scenario: First download of a season
- **GIVEN** the local cache does not contain `2024seve.zip`
- **WHEN** the user or pipeline requests 2024 event data
- **THEN** the client downloads `2024seve.zip` from retrosheet.org, verifies the archive, and extracts it to the cache.

#### Scenario: Repeated request uses cached data
- **GIVEN** `2024seve.zip` is already present and valid in the local cache
- **WHEN** the user requests 2024 event data without `--refresh`
- **THEN** no network request is made and the cached files are used directly.

#### Scenario: First download of a season via GitHub mirror
- **GIVEN** the local cache does not contain event data for year 2024
- **WHEN** the user requests 2024 event data with `source="github"` (or default "auto")
- **THEN** the client resolves the season manifest (`TEAM2024`), downloads uncompressed event and roster files via GitHub raw CDN, and populates the local cache directory.

#### Scenario: Fallback to retrosheet.org on mirror failure
- **GIVEN** the GitHub raw mirror returns an HTTP error or is unreachable
- **WHEN** the user requests a dataset with `source="auto"`
- **THEN** the system falls back to downloading the official archive bundle from `retrosheet.org`.

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

### Requirement: Database DDL Generation
The system MUST provide explicit SQL DDL generation for all Retrosheet datasets targeting PostgreSQL, DuckDB, and SQLite dialects so that DBAs can pre-create strongly-typed tables.

#### Scenario: Generating PostgreSQL DDL for events
- **WHEN** the user calls `rs.get_ddl("events", dialect="postgres")`
- **THEN** a valid `CREATE TABLE events (...)` SQL DDL string is returned containing correct PostgreSQL types (`DATE`, `SMALLINT`, `BOOLEAN`, `VARCHAR`).

### Requirement: Ingestion into Pre-Existing Database Tables
The system MUST support inserting parsed data into existing database tables without failing or dropping columns, aligning data by column name and using typed parameters.

#### Scenario: Inserting into pre-existing DuckDB table with custom schema
- **GIVEN** a DuckDB database with a pre-existing table `events`
- **WHEN** `rs.to_duckdb(path, years=[2024], mode="append")` is executed
- **THEN** data is appended matching column names without dropping or modifying the existing schema.

### Requirement: Cloud Warehouse Ingestion via dlt
The system MUST provide first-class `dlt` pipeline execution (`rs.to_dlt`) enabling direct automated loading into PostgreSQL, Snowflake, or BigQuery destinations, streaming native PyArrow Tables and RecordBatches directly to destinations without converting batches to row dictionaries.

#### Scenario: Running a dlt pipeline into PostgreSQL
- **GIVEN** a destination name or connection URL and selected years
- **WHEN** `rs.to_dlt(destination="duckdb", years=[2024], datasets=["parks"])` is called
- **THEN** a dlt pipeline executes and loads the data into the destination with verified schema contracts.

#### Scenario: Running a dlt pipeline with Arrow batches
- **GIVEN** a destination connection URL and selected datasets
- **WHEN** `rs.to_dlt(destination="duckdb", years=[2024], datasets=["parks"])` is called
- **THEN** the dlt source yields PyArrow Tables or RecordBatches directly to dlt and loads the data into the destination with typed schema contracts.

### Requirement: Legacy Dataset Handling and Deprecation Notice
The system MUST emit a clear deprecation warning when accessing legacy datasets that are no longer maintained upstream (specifically transactions discontinued in November 2021) and gracefully handle unavailable remote archives by allowing local file cache fallback.

#### Scenario: Accessing discontinued transactions dataset
- **WHEN** the user requests transactions data via `rs.transactions()`
- **THEN** a `FutureWarning` or deprecation notice is emitted informing the user that Retrosheet handed maintenance over to Baseball-Reference in November 2021.

#### Scenario: Graceful handling of unreachable transaction archive
- **GIVEN** `retrosheet.org` is unreachable and no local transactions file exists
- **WHEN** a bulk ingestion is requested that includes transactions with non-strict mode
- **THEN** the system warns and skips transactions rather than crashing the entire season ingestion pipeline.

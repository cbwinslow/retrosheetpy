# Spec Delta: retrosheet-ingestion

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Legacy Dataset Handling and Deprecation Notice
The system MUST emit a clear deprecation warning when accessing legacy datasets that are no longer maintained upstream (specifically transactions discontinued in November 2021) and gracefully handle unavailable remote archives by allowing local file cache fallback.

#### Scenario: Accessing discontinued transactions dataset
- **WHEN** the user requests transactions data via `rs.transactions()`
- **THEN** a `FutureWarning` or deprecation notice is emitted informing the user that Retrosheet handed maintenance over to Baseball-Reference in November 2021.

#### Scenario: Graceful handling of unreachable transaction archive
- **GIVEN** `retrosheet.org` is unreachable and no local transactions file exists
- **WHEN** a bulk ingestion is requested that includes transactions with non-strict mode
- **THEN** the system warns and skips transactions rather than crashing the entire season ingestion pipeline.

# Command-Line Interface (CLI)

`retrosheetpy` provides a lightning-fast CLI tool for downloading Retrosheet archives, ingesting into DuckDB or cloud warehouses, exporting to Parquet/CSV, generating production SQL DDL, and managing the local cache.

---

## Global Options

```bash
retrosheetpy [OPTIONS] COMMAND [ARGS]...
```

* `--version`: Show package version and exit.
* `--help`: Show help message and exit.

---

## `retrosheetpy download`

Downloads and caches specified Retrosheet archives locally without loading them into memory or writing to an external database:

```bash
retrosheetpy download [OPTIONS]
```

### Options
* `-s, --dataset [events|postseason|allstar|gamelogs|rosters|parks|schedules|bio|ejections|transactions|all]` *(Default: `all`)*: Dataset to download.
* `-y, --years TEXT` *(Optional)*: Year or range of years (e.g. `2024` or `2020-2024`).
* `-S, --source [github|retrosheet|auto]` *(Default: `github`)*: Authoritative download source. Defaults to Fastly-backed GitHub raw mirror (`chadwickbureau/retrosheet`).
* `--force`: Force re-download even if already cached.

### Examples
```bash
# Download and extract 2024 event files from GitHub mirror
retrosheetpy download -s events -y 2024 --source github

# Download all 2020-2024 archives into cache with automatic fallback
retrosheetpy download -s all -y 2020-2024 --source auto

# Download reference files (parks, biofile, ejections)
retrosheetpy download -s bio,parks,ejections
```

---

## `retrosheetpy ingest`

Downloads and ingests specified seasons and datasets directly into an embedded DuckDB database file or a remote cloud data warehouse via `dlt`:

```bash
retrosheetpy ingest [OPTIONS]
```

### Options
* `-d, --dest [duckdb|postgres|snowflake|bigquery|sqlite]` *(Default: `duckdb`)*: Destination database type.
* `-c, -f, --conn PATH/URI` *(Required)*: Output file path (for DuckDB/SQLite) or warehouse connection URI (for Postgres, Snowflake, BigQuery).
* `-s, --dataset TEXT` *(Default: `events,gamelogs,rosters,parks`)*: Comma-separated list of datasets to ingest, or `all`.
* `-y, --years TEXT` *(Default: `2024`)*: Year or range of years (e.g. `2024` or `2010-2024`).
* `-S, --source [github|retrosheet|auto]` *(Default: `github`)*: Download source mirror.
* `--force`: Force re-download even if already present in local cache.

### Examples
```bash
# Ingest 2020 through 2024 into local DuckDB
retrosheetpy ingest -d duckdb -c retro.duckdb -s events,gamelogs -y 2020-2024

# Ingest all 2024 data into PostgreSQL warehouse via dlt
retrosheetpy ingest -d postgres -c "postgresql://user:pass@localhost:5432/retrosheet" -s all -y 2024

# Ingest into Snowflake
retrosheetpy ingest -d snowflake -c "snowflake://..." -s gamelogs -y 2020-2024
```

---

## `retrosheetpy export`

Exports any Retrosheet dataset to compressed Parquet or CSV format:

```bash
retrosheetpy export [OPTIONS]
```

### Options
* `-s, --dataset [events|postseason|allstar|gamelogs|rosters|parks|schedules|bio|ejections|transactions]` *(Required)*: Dataset to export.
* `-y, --years TEXT` *(Default: `2024`)*: Year or range of years (e.g. `2024` or `2000-2024`).
* `-o, --output PATH` *(Required)*: Output file path (e.g. `gamelogs_2024.parquet`).
* `-f, -fmt, --format [parquet|csv]` *(Default: `parquet`)*: Output file format.
* `-S, --source [github|retrosheet|auto]` *(Default: `github`)*: Download source mirror.
* `--force`: Force re-download even if already present in local cache.

### Examples
```bash
# Export 2024 game logs to Parquet
retrosheetpy export -s gamelogs -y 2024 -f parquet -o gl2024.parquet

# Export 2024 schedules to Parquet
retrosheetpy export -s schedules -y 2024 -f parquet -o schedules_2024.parquet

# Export biographical master file to CSV
retrosheetpy export -s bio -f csv -o biofile.csv
```

---

## `retrosheetpy ddl`

Generates and prints the standard SQL DDL `CREATE TABLE` statement with strict native data types:

```bash
retrosheetpy ddl [OPTIONS]
```

### Options
* `-s, --dataset [events|postseason|allstar|gamelogs|rosters|parks|schedules|bio|ejections|transactions]` *(Required)*: Dataset name.
* `--dialect [postgres|duckdb|sqlite|snowflake|bigquery]` *(Default: `postgres`)*: Target database dialect.

### Examples
```bash
# Generate PostgreSQL DDL for events
retrosheetpy ddl -s events --dialect postgres

# Generate BigQuery DDL for schedules
retrosheetpy ddl -s schedules --dialect bigquery

# Generate Snowflake DDL for biofile
retrosheetpy ddl -s bio --dialect snowflake
```

---

## `retrosheetpy cache`

Inspects or clears the local download and decompression cache:

```bash
retrosheetpy cache [OPTIONS]
```

### Options
* `--clear`: Evict and clear all cached archives and decompressed files.
* *(no options)*: Prints cache directory location and total disk usage.

### Examples
```bash
# Inspect cache
retrosheetpy cache

# Clear cache
retrosheetpy cache --clear
```

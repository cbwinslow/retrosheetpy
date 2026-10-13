# Command-Line Interface (CLI)

`retrosheetpy` provides a fast CLI tool for ingesting into DuckDB, exporting to Parquet/CSV, generating SQL DDL, and managing the local cache.

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
* `-s, --dataset [events|gamelogs|rosters|parks|schedules|bio|all]` *(Default: `all`)*: Dataset to download.
* `-y, --years TEXT` *(Optional)*: Year or range of years (e.g. `2024` or `2020-2024`).
* `--force`: Force re-download even if already cached.

### Example
```bash
# Download and extract 2024 event files
retrosheetpy download --dataset events --years 2024

# Download all 2020-2024 archives into cache
retrosheetpy download --dataset all --years 2020-2024
```

---

## `retrosheetpy ingest`

Downloads and ingests specified seasons and datasets directly into an embedded DuckDB database file:

```bash
retrosheetpy ingest [OPTIONS]
```

### Options
* `-y, --years TEXT` *(Required)*: Year or range of years (e.g. `2024` or `2010-2024`).
* `-f, --file PATH` *(Required)*: Output database file path (e.g. `retrosheet.duckdb`).
* `-d, --dest [duckdb]` *(Default: `duckdb`)*: Destination database type.
* `-s, --datasets TEXT` *(Default: `events,gamelogs,rosters,parks`)*: Comma-separated list of datasets to ingest.
* `--force`: Force re-download even if already present in local cache.

### Example
```bash
# Ingest 2020 through 2024 into retro.duckdb
retrosheetpy ingest --years 2020-2024 --dest duckdb --file retro.duckdb
```

---

## `retrosheetpy export`

Exports a Retrosheet dataset to compressed Parquet or CSV format:

```bash
retrosheetpy export [OPTIONS]
```

### Options
* `-s, --dataset [events|gamelogs|rosters|parks]` *(Required)*: Dataset to export.
* `-y, --years TEXT` *(Default: `2024`)*: Year or range of years (e.g. `2024` or `2000-2024`).
* `-o, --output PATH` *(Required)*: Output file path (e.g. `gamelogs_2024.parquet`).
* `-fmt, --format [parquet|csv]` *(Default: `parquet`)*: Output file format.
* `--force`: Force re-download even if already present in local cache.

### Example
```bash
# Export 2024 game logs to Parquet
retrosheetpy export --dataset gamelogs --years 2024 --format parquet --output gl2024.parquet

# Export 2024 rosters to CSV
retrosheetpy export --dataset rosters --years 2024 --format csv --output rosters2024.csv
```

---

## `retrosheetpy ddl`

Generates and prints the standard SQL DDL `CREATE TABLE` statement for a dataset:

```bash
retrosheetpy ddl [OPTIONS]
```

### Options
* `-s, --dataset [events|gamelogs|rosters|parks]` *(Required)*: Dataset name.
* `--dialect [postgres|duckdb|sqlite]` *(Default: `postgres`)*: Target database dialect.

### Example
```bash
retrosheetpy ddl --dataset gamelogs --dialect postgres
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

### Example
```bash
# Inspect cache
retrosheetpy cache

# Clear cache
retrosheetpy cache --clear
```

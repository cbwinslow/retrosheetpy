# Design: SQL & dlt Database Ingestion and Exhaustive Testing

## Architecture & Design Decisions

### 1. SQL DDL Generation (`src/retrosheetpy/schemas/ddl.py`)
To empower DBAs who want to pre-create tables in PostgreSQL, SQLite, or DuckDB before running ingestion jobs:
- Type mapping table translating PyArrow data types to SQL dialect types:
  - `date32()` $\to$ `DATE`
  - `int8()` $\to$ `SMALLINT` (Postgres) / `TINYINT` (DuckDB) / `INTEGER` (SQLite)
  - `int16()` $\to$ `SMALLINT`
  - `int32()` $\to$ `INTEGER`
  - `bool_()` $\to$ `BOOLEAN`
  - `string()` $\to$ `VARCHAR` / `TEXT`
- Helper function: `generate_ddl(dataset: str, dialect: str = "postgres") -> str`

### 2. Pre-Existing Table Alignment
When inserting into an existing table in DuckDB or SQL:
- Query existing table columns from `information_schema.columns` or `pragma_table_info`.
- Match Arrow table columns by name to destination table columns.
- Issue explicit column-listed `INSERT INTO <table> (col1, col2, ...) SELECT col1, col2, ... FROM ...` rather than blind `INSERT INTO <table> SELECT *`.
- This ensures that if a DBA reordered columns or added extra generated columns with defaults (e.g. `ingested_at TIMESTAMP DEFAULT now()`), the ingestion succeeds seamlessly.

### 3. High-Level `dlt` Ingestion Runner (`rs.to_dlt`)
- Expose `to_dlt(destination: str | Any, years: int | Sequence[int], datasets: Sequence[str] = ..., pipeline_name: str = "retrosheet", **dlt_kwargs) -> Any`:
  - Instantiates `dlt.pipeline(pipeline_name=pipeline_name, destination=destination, **dlt_kwargs)`.
  - Runs the pipeline with `retrosheet_source(years=years, datasets=datasets)`.
  - Returns the `dlt.LoadInfo` object so callers can inspect rows loaded, schema updates, and execution status.

### 4. Integration Test Suite on `cbwsff1` (Live PostgreSQL via Docker)
- Launch a lightweight PostgreSQL container on `cbwsff1` (`docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:alpine`).
- Run a live test ingesting 2024 Retrosheet game logs and rosters into PostgreSQL using `dlt` and verifying table creation, data types, and row counts.
- Tear down the test container after verification.

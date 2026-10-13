# Proposal: SQL & dlt Database Ingestion and Exhaustive Testing

## Why
Baseball analysts, professors, and DBAs require seamless ingestion of Retrosheet data into external relational databases (PostgreSQL, SQLite, MySQL, Snowflake, BigQuery) where schemas may already be established by database administrators. Currently, users need explicit DDL generation tools, resilient ingestion into pre-existing tables without type errors, verified `dlt` cloud warehouse pipelines, and exhaustive integration testing across historical eras.

## What Changes
- **SQL DDL Generator**: Expose `rs.get_ddl(dataset, dialect="postgres"|"duckdb"|"sqlite")` generating valid SQL DDL statements with precise column types for DBAs.
- **Pre-Existing Table Ingestion**: Ensure SQL and DuckDB ingestors support column-name aligned inserts and verify that pre-created schemas are respected rather than overwritten or failing on column order.
- **Verified `dlt` Pipeline**: Expose `rs.to_dlt(destination, years, datasets=...)` with schema contract options (`freeze` or `evolve`), supporting live Postgres, Snowflake, and BigQuery destinations.
- **Expanded CLI & Ingestion Targets**: Enhance `retrosheetpy ingest` to support `--dest sqlite`, `--dest postgres` (via connection URL or DuckDB scanner), and `--dest dlt`.
- **Exhaustive Testing & Verification**: Comprehensive test coverage for all edge cases (doubleheaders, rainouts, rosters, park codes, Negro leagues), plus live PostgreSQL verification via Docker on `cbwsff1`.

## Capabilities

### Modified Capabilities
- `retrosheet-ingestion`: Add requirements for DDL generation, pre-existing table schema alignment, and automated `dlt` cloud warehouse execution.

## Impact
- Adds `src/retrosheetpy/schemas/ddl.py` for SQL DDL generation.
- Adds `to_dlt` and `to_sql` helpers in `src/retrosheetpy/api.py` and CLI options in `cli.py`.
- Expands test coverage across all dataset parsers and sinks.

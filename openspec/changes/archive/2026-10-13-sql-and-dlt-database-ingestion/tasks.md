# Tasks: SQL & dlt Database Ingestion and Exhaustive Testing

## Tasks
- [x] 1. Implement SQL DDL generator in `src/retrosheetpy/schemas/ddl.py` with dialect support for PostgreSQL, DuckDB, and SQLite.
- [x] 2. Update `DuckDBSink` to support column-name matching when inserting into pre-existing tables.
- [x] 3. Implement high-level `to_dlt()` in `src/retrosheetpy/api.py` and export in top-level `__init__.py`.
- [x] 4. Enhance CLI with `--dest sqlite` and `--dest dlt` options.
- [x] 5. Write comprehensive unit tests for DDL generation and pre-existing table appends in `tests/test_ddl.py`.
- [x] 6. Run live PostgreSQL integration test on `cbwsff1` using Docker.

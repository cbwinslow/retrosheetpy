# Tasks: Initial Architecture & Ingestion Pipeline

## Tasks
- [x] 1. Project setup: directory structure, `src/retrosheetpy/`, tests directory, `pyproject.toml` dependencies with `uv`.
- [x] 2. Implement `extract/`: Retrosheet URL manifest, downloader, and cache manager with tests.
- [x] 3. Implement `schemas/`: strongly typed PyArrow schemas for events (164 fields), game logs (161 fields), rosters, parks, and bio.
- [x] 4. Implement `parse/`:
  - [x] 4.1. Chadwick event parser adapter (calling `chadwickpy` and producing typed Arrow batches).
  - [x] 4.2. Game log parser (parsing `glYYYY.txt` into typed Arrow tables).
  - [x] 4.3. Roster, park, and bio parser.
- [x] 5. Implement `sink/`:
  - [x] 5.1. DuckDB sink (direct table append / create).
  - [x] 5.2. Parquet / CSV sink.
  - [x] 5.3. DataFrame converters (Polars, Arrow, pandas).
  - [x] 5.4. Optional `dlt` source and resource definitions.
- [x] 6. Implement `api.py` and top-level `__init__.py` namespace (`rs.events()`, `rs.game_logs()`, etc.).
- [x] 7. Implement CLI `cli.py` with Click/Rich.
- [x] 8. End-to-end integration tests (local fixtures and remote test script on `cbwsff1`).

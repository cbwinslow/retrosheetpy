# retrosheetpy constitution

## What it is
`retrosheetpy` is an end-to-end, high-performance, and modular Python library and CLI
for baseball analysts, researchers, professors, and database administrators.

It automatically downloads, caches, parses, and ingests all Retrosheet datasets:
- **Play-by-Play Event Data**: Parsed via `chadwickpy` (events, games, daily player lines, substitutions, comments, box scores).
- **Historical Game Logs (1871–present)**: 161+ columns of game scores, line scores, attendance, starting pitchers, and umpires.
- **Rosters & Schedules**: Season rosters (`.ROS`), schedules (`sked`), and alignments.
- **Biographical & Directory Records**: Player biography (`biofile`/people), ballparks (`parks`), transactions, and ejections.

## Boundaries & Architecture
```text
chadwickpy   = pure-Python port of Chadwick C tools (the parser engine). Zero network, zero storage.
retrosheetpy = downloads Retrosheet files, caches locally, parses via chadwickpy & native parsers,
               coerces into strongly-typed schemas (Dates, Integers, Booleans, Floats), and emits to
               DuckDB, Parquet, Arrow, Polars, pandas, and SQL/dlt.
mlb-baseball = downstream consumer / database deployment using retrosheetpy.
```
Dependency direction: `mlb-baseball` -> `retrosheetpy` -> `chadwickpy`. Never the reverse.

## Invariants
1. **Strongly-Typed Schemas, Never Raw Text**: Retrosheet text files must be parsed into rich types (e.g. `DATE`, `INTEGER`, `BOOLEAN`, `FLOAT`, `VARCHAR`) across all export formats (DuckDB, Parquet, PyArrow, Polars).
2. **Decoupled Architecture**: Extract (download/cache), Parse (transform/schema), and Sink (DuckDB/Parquet/Arrow/dlt) are separated by Python Protocols so any component can be swapped without changing client APIs.
3. **Smart Local Caching**: Never re-download raw files unless explicitly requested or hashes differ. Cache resides in user-configurable directories (`~/.cache/retrosheetpy`).
4. **Developer-Friendly Namespace**: Expose an intuitive, discoverable Python API (`rs.events()`, `rs.game_logs()`, `rs.rosters()`, `rs.to_duckdb()`) and a companion CLI (`retrosheetpy ingest`, `retrosheetpy export`).
5. **No C Compiler Required**: Must be installable with standard `pip install retrosheetpy` or `uv add retrosheetpy` on Windows, macOS, and Linux without native build toolchains.
6. **Multi-Era Robustness**: Handle historical data anomalies, era changes, and format evolutions gracefully with versioned schemas.

## Phases
- **Phase 1: Project Scaffolding & Specifications**: OpenSpec baseline, specs for Extract, Schema/Parse, and Sink.
- **Phase 2: Extract & Cache Engine**: Downloaders with HTTP connection pooling, retry logic, unzip handlers, and cache managers.
- **Phase 3: Schema & Parsing Layer**: Typed PyArrow schemas for Chadwick outputs, game logs, rosters, and biofiles.
- **Phase 4: Sinks (DuckDB, Parquet, Polars/pandas, dlt)**: Ingestion drivers and export routines.
- **Phase 5: CLI & Python API**: Unified `retrosheetpy` CLI and top-level namespace.
- **Phase 6: Verification & Publishing**: Integration test suite run against `cbwsff1`, docs on GitHub Pages, PyPI release.

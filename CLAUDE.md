# retrosheetpy Development Guide

## Commands
- **Environment & Tests:**
  - Setup: `uv sync --all-extras`
  - Run all tests: `uv run pytest`
  - Run specific test: `uv run pytest tests/test_extract.py -k "test_download"`
  - Formatting & Linting: `uvx ruff check .` and `uvx ruff format .`
  - Type checking: `uv run mypy src`
- **CLI Usage:**
  - `uv run retrosheetpy --help`
  - `uv run retrosheetpy download --years 2024 --dataset events`
  - `uv run retrosheetpy ingest --years 2024 --dest duckdb --file baseball.duckdb`

## Architecture
- `src/retrosheetpy/extract/`: HTTP client, download caching, decompression, Retrosheet URL registry.
- `src/retrosheetpy/schemas/`: Explicit PyArrow / DuckDB typed schemas for every dataset.
- `src/retrosheetpy/parse/`: Parsers for event files (via `chadwickpy`), game logs, rosters, ballparks, etc.
- `src/retrosheetpy/sink/`: Output writers (PyArrow, DuckDB, Parquet, CSV, and optional `dlt`).
- `src/retrosheetpy/api.py`: High-level Python user interface (`import retrosheetpy as rs`).
- `src/retrosheetpy/cli.py`: Command-line tool.

## Key Design Principles
1. **Never untyped text in databases**: All fields must parse into dates, integers, floats, booleans, or strings.
2. **Decoupled stages**: Extract, Parse, and Sink must communicate only through typed records or Arrow RecordBatches.
3. **Smart caching**: Cache raw and decompressed files in `~/.cache/retrosheetpy/` to respect Retrosheet server bandwidth.

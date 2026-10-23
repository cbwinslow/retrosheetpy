# Tasks: GitHub Downloader & Modern Ingestion Stack

## 1. Dependencies and Configuration Models

- [x] 1.1 Update `pyproject.toml` to promote `polars` and `dlt` to core `dependencies` and add `pydantic>=2.0.0`; verify with `uv sync --all-extras`.
- [x] 1.2 Implement Pydantic V2 configuration models (`DownloaderConfig`, `IngestionConfig`) in `src/retrosheetpy/extract/config.py`; verify with unit tests.

## 2. Multi-Source Downloader & GitHub CDN Integration

- [x] 2.1 Update `src/retrosheetpy/extract/manifest.py` with GitHub CDN endpoints for reference datasets, seasons, and game logs; verify with manifest URL unit tests.
- [x] 2.2 Refactor `src/retrosheetpy/extract/downloader.py` to support `source="github" | "retrosheet" | "auto"` with GitHub Fastly raw CDN fetching, season `TEAM{year}` manifest resolution, and fallback resilience; verify with mocked HTTP unit tests.
- [x] 2.3 Implement deprecation notices and graceful cache fallbacks for `rs.transactions()` in `src/retrosheetpy/api.py` and `downloader.py`; verify warning emission with unit tests.
- [x] 2.4 Update top-level APIs (`events`, `gamelogs`, `rosters`, `schedules`, `parks`, `bio`, `ejections`, `download`) and CLI in `src/retrosheetpy/cli.py` with `--source`; verify CLI options with tests.

## 3. High-Performance Arrow-Native `dlt` Ingestion

- [x] 3.1 Refactor `src/retrosheetpy/sink/dlt_sink.py` to yield PyArrow Tables/Batches directly to `dlt` resources; verify dlt duckdb pipeline runs without row-dict conversions.
- [x] 3.2 Ensure `rs.to_dlt()` and `rs.to_duckdb()` seamlessly ingest GitHub-downloaded datasets; verify integration tests in `tests/test_sink.py`.

## 4. Documentation, Architectural Records & Verification

- [x] 4.1 Record architecture decisions and Retrosheet transaction handover in `docs/DECISIONS.md`.
- [x] 4.2 Update MkDocs documentation (`docs/index.md`, `docs/cli.md`, `docs/storage/dlt.md`) to document GitHub CDN downloads, source options, and the modern ingestion stack.
- [x] 4.3 Run full test suite, linting, and type checking (`uv run pytest`, `uvx ruff check .`, `uvx mypy --strict src`).

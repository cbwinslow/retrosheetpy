# Proposal: GitHub Downloader & Modern Ingestion Stack

## Why

`retrosheet.org` actively blocks and drops automated bulk downloading traffic, instructing users and automated libraries to retrieve Retrosheet data from GitHub mirrors such as the Chadwick Baseball Bureau (`chadwickbureau/retrosheet`). Furthermore, Retrosheet discontinued updating its historical transaction database (`tran.txt`) in November 2021, handing off ongoing tracking to Baseball-Reference. At the same time, users need out-of-the-box, strongly-typed ingestion into DuckDB, Polars, and cloud data warehouses via `dlt` without having to configure optional extras or endure slow Python dictionary serialization.

## What Changes

- **GitHub-First Multi-Source Downloader**: Default download source to GitHub raw CDN (`chadwickbureau/retrosheet`), supporting `source="github" | "retrosheet" | "auto"` in both Python API and CLI (`--source`).
- **Zero-Token Fastly Raw CDN Fetching**: Retrieve season event files, rosters, schedules, game logs, ballparks, biofiles, and ejections from GitHub raw CDN using `TEAM{year}` manifest lookups without hitting GitHub REST API 60 req/hr rate limits.
- **Legacy Transaction Dataset Handling**: Mark `rs.transactions()` as frozen/deprecated with documentation explaining Retrosheet's 2021 handover to Baseball-Reference; support local file loading and graceful fallback if `retrosheet.org` is unreachable.
- **Core Dependency Expansion**: Promote `polars` and `dlt` to core package dependencies alongside `pyarrow` and `duckdb`. Add `pydantic>=2.0.0` for structured configuration validation (`DownloaderConfig`, `IngestionConfig`).
- **High-Performance Arrow-Native `dlt` Ingestion**: Refactor `dlt_sink.py` resources to yield PyArrow Tables/Batches directly to `dlt` rather than converting to row dictionaries (`to_pylist()`), preserving rich Arrow types and eliminating memory overhead.
- **Documentation & Architecture Records**: Record architectural decisions in `docs/DECISIONS.md`, update MkDocs documentation, and refresh CLI reference guides.

## Capabilities

### Modified Capabilities
- `retrosheet-ingestion`: Update requirements to support multi-source downloading (GitHub primary, retrosheet.org fallback), explicit handling for frozen transactions, and zero-copy PyArrow streaming in `dlt` warehouse ingestion.

## Impact

- `src/retrosheetpy/extract/manifest.py`: Add GitHub raw CDN endpoint templates for reference tables, seasons, and game logs.
- `src/retrosheetpy/extract/downloader.py`: Implement multi-source resolution, manifest-driven file downloads, and fallback resilience.
- `src/retrosheetpy/sink/dlt_sink.py`: Stream native PyArrow Tables to `dlt` resources.
- `src/retrosheetpy/api.py` & `cli.py`: Expose `--source` / `source` parameter and update transaction warnings.
- `pyproject.toml`: Add `polars`, `dlt`, and `pydantic` to core `dependencies`.
- `docs/DECISIONS.md` & `docs/`: Update architecture records and user guides.

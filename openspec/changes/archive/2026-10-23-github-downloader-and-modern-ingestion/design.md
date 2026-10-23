# Design: GitHub Downloader & Modern Ingestion Stack

## Context

`retrosheetpy` currently downloads zip archives directly from `www.retrosheet.org`. Due to aggressive anti-scraping measures on the upstream web server, automated downloads encounter TCP SYN drops (connection timeouts). The Chadwick Baseball Bureau maintains an active, public mirror (`chadwickbureau/retrosheet`) containing the exact upstream files (`official` branch) and augmented files (`master` branch). Furthermore, the `transactions` database was discontinued upstream in November 2021, and the ingestion layer requires out-of-the-box support for `dlt` and `polars` with zero-copy PyArrow streaming.

## Goals / Non-Goals

**Goals:**
- Provide a robust multi-source downloader defaulting to GitHub Fastly raw CDN (`raw.githubusercontent.com/chadwickbureau/retrosheet`), with automatic fallback to `retrosheet.org` or user-configured mirror URLs.
- Ensure the downloaded files populate the local cache (`~/.cache/retrosheetpy`) in the exact folder structure expected by existing parsers ([`EventParser`](file:///c:/Users/blain/projects/retrosheetpy/src/retrosheetpy/parse/events.py), [`GameLogParser`](file:///c:/Users/blain/projects/retrosheetpy/src/retrosheetpy/parse/gamelogs.py), [`RosterParser`](file:///c:/Users/blain/projects/retrosheetpy/src/retrosheetpy/parse/rosters.py), [`ParkParser`](file:///c:/Users/blain/projects/retrosheetpy/src/retrosheetpy/parse/parks.py), [`BioParser`](file:///c:/Users/blain/projects/retrosheetpy/src/retrosheetpy/parse/bio.py)).
- Require zero GitHub personal access tokens by fetching static files via CDN and parsing season `TEAM{year}` manifests.
- Formalize transaction dataset deprecation with graceful fallback when remote archives are unreachable.
- Promote `polars` and `dlt` to core package dependencies in `pyproject.toml`, and introduce `pydantic` for configuration validation.
- Modernize `dlt_sink.py` to yield PyArrow Tables/Batches directly to `dlt` rather than serializing to row dictionaries.

**Non-Goals:**
- Modifying underlying event file parsing logic (which delegates to `chadwickpy`).
- Changing PyArrow schema contracts or breaking downstream table interfaces.
- Re-hosting third-party transaction databases outside Retrosheet's historical scope.

## Decisions

### Decision 1: Raw GitHub CDN over GitHub REST API
* **Choice:** Use `https://raw.githubusercontent.com/chadwickbureau/retrosheet/master/...` instead of the GitHub Contents REST API (`api.github.com`).
* **Rationale:** The GitHub REST API imposes a strict 60 requests/hour limit on unauthenticated clients. In contrast, `raw.githubusercontent.com` is backed by Fastly CDN, provides high throughput, requires no authentication, and handles bulk downloads seamlessly.
* **Alternative Considered:** Requiring user GitHub tokens (`GH_TOKEN`). Rejected as unnecessary overhead for public open-source baseball data.

### Decision 2: Season Manifest Resolution via `TEAM{year}`
* **Choice:** For season event files (`.EVA`, `.EVN`, `.ROS`), the downloader first fetches `seasons/{year}/TEAM{year}` to dynamically discover the list of active teams and leagues for that season, then downloads the respective team files and schedules.
* **Rationale:** Team alignments and counts change across eras (e.g. 16 teams in the 1950s vs. 30 teams today). Reading `TEAM{year}` guarantees exact file discovery across any historical season without hardcoding team codes or hitting directory listing endpoints.
* **Alternative Considered:** Scraping directory HTML or pre-generating a static JSON file map for all 150+ seasons. Using `TEAM{year}` uses Retrosheet's own native discovery file.

### Decision 3: Pydantic V2 for Configuration Only
* **Choice:** Introduce `pydantic>=2.0.0` for `DownloaderConfig`, `IngestConfig`, and connection parameters. Do not instantiate Pydantic models for individual pitch or event records.
* **Rationale:** Instantiating Pydantic models across millions of play-by-play rows causes a 100x slowdown. PyArrow columnar schema validation already guarantees strict, zero-overhead type enforcement for datasets.

### Decision 4: Native PyArrow Streaming in `dlt`
* **Choice:** Refactor `src/retrosheetpy/sink/dlt_sink.py` to yield `pa.Table` or `pa.RecordBatch` directly to `@dlt.resource`.
* **Rationale:** `dlt` has built-in zero-copy support for PyArrow. Streaming Arrow tables avoids expensive `to_pylist()` Python dictionary conversions and preserves precise Arrow types (such as `date32` and `int16`) when loading into DuckDB or PostgreSQL.

### Decision 5: Deprecate `transactions` Gracefully
* **Choice:** Mark `rs.transactions()` with a deprecation warning citing Retrosheet's November 2021 discontinuation and transition to Baseball-Reference. Provide local file cache resolution (`~/.cache/retrosheetpy/transactions/tran.txt`) and allow bulk ingestion to skip transactions without aborting the pipeline when `retrosheet.org` times out.

## Risks / Trade-offs

- **[Risk: GitHub raw CDN intermittent connection errors]** → Mitigation: Implement HTTP retry logic with exponential backoff using `httpx` transport retries and automatic fallback to `retrosheet.org` or custom mirror URLs.
- **[Risk: Season event file download volume]** → Mitigation: Ensure cache manager verifies existing extracted directory before requesting remote files (`is_extracted("events", year)`), preventing redundant network downloads.
- **[Risk: dlt dependency footprint]** → Mitigation: Modern `dlt` with `duckdb` and `postgres` dependencies integrates cleanly with Python 3.11+ and provides robust database loading.

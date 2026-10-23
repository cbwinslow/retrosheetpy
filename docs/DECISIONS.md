# Architecture Decision Records (ADRs)

This document records key architectural decisions, rationales, and upstream context for `retrosheetpy`.

---

## ADR 1: Multi-Source Download Strategy (GitHub Fastly CDN as Primary)

* **Date:** 2026-10-23
* **Status:** Accepted

### Context
`retrosheet.org` implements strict anti-scraping policies that drop TCP SYN connections on automated bulk requests, causing persistent connection timeouts for users and automated pipelines. Upstream Retrosheet notices guide users to retrieve data via GitHub mirrors. The Chadwick Baseball Bureau maintains a public, version-controlled GitHub mirror (`chadwickbureau/retrosheet`) tracking upstream Retrosheet data.

### Decision
1. Default `retrosheetpy` download source to the Fastly-backed GitHub raw CDN (`https://raw.githubusercontent.com/chadwickbureau/retrosheet/master/`).
2. Provide an `"auto"` mode that tries the GitHub CDN first and transparently falls back to `retrosheet.org` if needed.
3. Allow users to select `"github"`, `"retrosheet"`, or `"auto"` via `source` parameter or `--source` CLI flag.
4. Do not require personal GitHub tokens for downloading, as the raw CDN serves static files without consuming unauthenticated GitHub REST API rate limits (60 req/hr).

---

## ADR 2: Dynamic Season Discovery via `TEAM{year}` Manifest

* **Date:** 2026-10-23
* **Status:** Accepted

### Context
Major League Baseball has changed team configurations, franchise locations, and league alignments repeatedly since 1871 (from 12–16 franchises in early eras to 30 modern franchises). Hardcoding team lists or attempting directory scraping causes omissions or brittle breakage across historical seasons.

### Decision
For any requested season, the downloader retrieves `seasons/{year}/TEAM{year}`. It parses the team codes and leagues (`A` for American League, `N` for National League), and downloads `{year}{team}.EVA` / `{year}{team}.EVN` and `{team}{year}.ROS` accordingly. This matches Retrosheet's native catalog format and works seamlessly with `chadwickpy.roster.League`.

---

## ADR 3: Upstream Transactions Freeze & Handover to Baseball-Reference

* **Date:** 2026-10-23
* **Status:** Accepted

### Context
Retrosheet discontinued maintaining and updating its standalone transaction files (`tran.txt` / `tranDB.zip`) on November 26, 2021. Upstream responsibility for MLB transaction records was formally transitioned to Baseball-Reference.

### Decision
1. Issue a `FutureWarning` when `rs.transactions()` is invoked, informing the user that the dataset is frozen as of November 26, 2021.
2. Allow users to provide a local file override (`~/.cache/retrosheetpy/transactions/tran.txt`).
3. For bulk ingestion and downloading pipelines (`rs.download(datasets='all')` or `rs.to_duckdb(datasets='all')`), catch unreachable remote errors for transactions and emit a warning rather than failing the entire pipeline.

---

## ADR 4: Promotion of `polars` and `dlt` to Core Dependencies

* **Date:** 2026-10-23
* **Status:** Accepted

### Context
Baseball researchers and data engineers increasingly use modern data stacks centered on Polars, DuckDB, and `dlt` for direct loading into PostgreSQL, Snowflake, and BigQuery. Previously, `polars` and `dlt` were optional extras, requiring separate installation steps and causing runtime `ImportError` exceptions when users attempted `rs.to_polars()` or `rs.to_dlt()`.

### Decision
Promote `polars>=1.0.0` and `dlt[duckdb,postgres,snowflake]>=1.0.0` to core `dependencies` in `pyproject.toml`. Retain `pandas` as an optional dependency for legacy workloads.

---

## ADR 5: Pydantic V2 for Configuration vs. PyArrow for Columnar Data

* **Date:** 2026-10-23
* **Status:** Accepted

### Context
Retrosheet play-by-play files contain tens of millions of pitch and event records. Instantiating row-level Pydantic models introduces massive CPU overhead (100x slowdown) and memory consumption. However, structured configuration (download sources, cache parameters, connection strings) benefits significantly from Pydantic V2 validation.

### Decision
1. Use Pydantic V2 (`BaseModel`) strictly for configuration models: `DownloaderConfig` and `IngestionConfig` in `retrosheetpy.extract.config`.
2. Keep all tabular event and game records in columnar PyArrow Tables and RecordBatches.

---

## ADR 6: Zero-Copy PyArrow Streaming into `dlt` Resources

* **Date:** 2026-10-23
* **Status:** Accepted

### Context
Previously, `dlt_sink.py` converted PyArrow Table batches to Python dictionaries (`for batch in tbl.to_batches(): yield from batch.to_pylist()`). This discarded PyArrow types (such as `date32` and `int16`), caused memory bloat, and slowed down loading into DuckDB or PostgreSQL.

### Decision
Refactor all `@dlt.resource` definitions in `src/retrosheetpy/sink/dlt_sink.py` to yield PyArrow Tables (`pa.Table`) directly. `dlt` natively consumes Arrow tables and batches with zero-copy throughput.

---

## ADR 7: HTTP Session Pooling and Resilient Season Extraction

* **Date:** 2026-10-23
* **Status:** Accepted

### Context
When downloading uncompressed seasons via the GitHub raw CDN, `Downloader` requests ~60 files per season (team manifests, individual team event files, and rosters). Recreating `httpx.Client()` on each request introduced connection overhead. Furthermore, raw download loops previously swallowed all exceptions indiscriminately, risking partial cache directories during network dropouts.

### Decision
1. Lazily manage a persistent `httpx.Client` on `Downloader` with connection pooling, and implement `close()`, `__enter__`, `__exit__`, and `__del__` for resource cleanup.
2. In `_get_events_github`, distinguish expected HTTP 404s (teams with no separate event files) from network transport/timeout errors. Network errors immediately raise and clean up partial season directories to prevent cache corruption.

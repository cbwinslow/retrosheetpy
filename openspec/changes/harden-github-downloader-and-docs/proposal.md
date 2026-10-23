# Proposal: Harden GitHub Raw CDN Downloader, Fix Inconsistencies, and Modernize HTTP Client

## Why
A recent feature commit introduced the GitHub raw CDN mirror (`chadwickbureau/retrosheet`) alongside the promotion of `dlt`, `polars`, and `pydantic` into core dependencies. However, strict architectural and code review identified three high-priority reliability and usability gaps:
1. `_get_events_github` in `downloader.py` unconditionally swallows all exceptions (`except Exception: pass`) when downloading individual team event (`.EVA`/`.EVN`) and roster (`.ROS`) files. Network dropouts or timeouts are masked, creating silently corrupted or incomplete cached seasons rather than properly raising or triggering automatic fallback to `retrosheet.org`.
2. `_fetch_bytes` instantiates and tears down a brand new `httpx.Client()` context on every single HTTP GET. A full season raw fetch requires ~60 sequential requests, incurring massive TCP/TLS connection handshake overhead.
3. Inconsistencies exist across docs and code: `CLAUDE.md` uses an invalid CLI flag (`--file` instead of `--conn` / `-f`), and import error messages in `dlt_sink.py` and `api.py` instruct users to install `retrosheetpy[dlt]`, an extra that was eliminated when `dlt` became a core dependency.

Resolving these issues ensures that raw CDN extraction is bulletproof, fast, and completely consistent with documentation and CLI contracts.

## What Changes
- **Resilient Error Handling in Downloader**:
  - Distinguish between expected missing files (HTTP 404 for split seasons or non-participating teams) and actual network/connection failures (`httpx.TransportError`, `httpx.TimeoutException`, non-404 HTTP errors).
  - Ensure that network failures during individual team downloads fail fast in `source="github"` or trigger fallback to `retrosheet.org` in `source="auto"`.
  - Validate that at least one event file was successfully downloaded before marking a season cache directory as valid.
- **HTTP Client Session Pooling**:
  - Add persistent session reuse in `Downloader` using a reusable/context-managed `httpx.Client` to exploit HTTP Keep-Alive / connection pooling across multi-file season downloads.
- **Documentation & Error Message Alignment**:
  - Fix `CLAUDE.md` CLI ingestion example to use `--conn` / `-f` instead of `--file`.
  - Update `CLAUDE.md` to reflect new default source configuration (`--source [github|retrosheet|auto]`) and core dependencies.
  - Fix `dlt` import error guidance in `dlt_sink.py` and `api.py` to reference `pip install dlt` instead of non-existent extra `retrosheetpy[dlt]`.

## Capabilities

### Modified Capabilities
- `retrosheet-ingestion`: Update requirements and scenarios for download resilience and connection management under the GitHub raw mirror.

## Impact
- **Affected Code**:
  - `src/retrosheetpy/extract/downloader.py`
  - `src/retrosheetpy/sink/dlt_sink.py`
  - `src/retrosheetpy/api.py`
  - `CLAUDE.md`
- **APIs**: No breaking API changes; `Downloader` and API entrypoints retain backward-compatible signatures.
- **Dependencies**: No new dependencies added; leverages existing `httpx`.

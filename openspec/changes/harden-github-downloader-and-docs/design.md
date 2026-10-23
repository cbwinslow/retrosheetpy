# Design

## Context
See `proposal.md` for overall motivation. `Downloader` handles file retrieval from both `retrosheet.org` archives and GitHub raw CDN mirrors (`chadwickbureau/retrosheet`). Currently, `Downloader._fetch_bytes` creates a new `httpx.Client` per GET request, and `_get_events_github` uses bare `try ... except Exception: pass` blocks around each team's `.EVA`/`.EVN`/`.ROS` download, masking network dropouts and creating incomplete season directories in cache. In addition, documentation and error message inconsistencies must be aligned with recent dependency promotions (`dlt`, `polars`).

## Goals / Non-Goals

**Goals:**
- Provide connection-pooled HTTP client access in `Downloader` via a reusable `httpx.Client` session or context manager.
- Differentiate between expected 404s (e.g., historical seasons where a team listed in `TEAM{year}` played all neutral games or lacks an event file) and network transport/timeout errors.
- Ensure any network error during raw season extraction either raises directly (when `source="github"`) or cleanly triggers fallback to `retrosheet.org` archive bundle without leaving incomplete artifacts in cache (when `source="auto"`).
- Align `CLAUDE.md`, `dlt_sink.py`, and `api.py` with the CLI flags and core dependency status.

**Non-Goals:**
- Async multi-threaded concurrency for team downloads in this iteration (kept synchronous with connection keep-alive to avoid race conditions and maintain Windows/Python 3.11+ cross-platform simplicity).
- Changing Chadwick event parser interface.

## Decisions

### Decision 1: Shared `httpx.Client` with lazy initialization and cleanup
- **Choice**: Manage an internal `_client: httpx.Client | None` on `Downloader`. Add a `close()` method and context manager support (`__enter__`, `__exit__`), while keeping `_fetch_bytes` safe for unmanaged standalone usage by creating a default client if none is active.
- **Rationale**: Reusing TCP connections with HTTP Keep-Alive dramatically reduces latency when downloading 30+ team files sequentially from Fastly raw CDN.
- **Alternative considered**: Requiring all callers to use `with Downloader() as dl:`—rejected because it would break existing public API usages like `dl = Downloader(); dl.get_parks()`.

### Decision 2: Specific Exception Handling in `_get_events_github`
- **Choice**:
  ```python
  try:
      event_bytes = self._fetch_bytes(url)
      (extracted_dir / filename).write_bytes(event_bytes)
  except httpx.HTTPStatusError as err:
      if err.response.status_code == 404:
          pass  # Expected: team has no separate event file
      else:
          raise
  except (httpx.TransportError, httpx.TimeoutException):
      raise
  ```
  If a network exception or non-404 error occurs, clean up any partial `extracted_dir` files and re-raise. Under `source="auto"`, the outer caller catches and falls back to `retrosheet.org`. Under `source="github"`, it surfaces the network error.
- **Rationale**: Prevents cache poisoning where a season directory contains only a subset of teams and is falsely deemed complete by `is_extracted`.

### Decision 3: CLI & Error Message Corrections
- **Choice**: Fix `CLAUDE.md` to show `uv run retrosheetpy ingest --years 2024 --dest duckdb --conn baseball.duckdb` (or `-c`), update the default source description, and change `dlt` import error text to `pip install dlt`.
- **Rationale**: Strict alignment with actual CLI options (`--conn`, `-c`, `-f`) and current `pyproject.toml` dependencies.

## Risks / Trade-offs

- **[Risk] An unclosed `httpx.Client` session on interpreter shutdown** → **Mitigation**: Implement `__del__` safety fallback and ensure standard library `warnings` or finalizers cleanly release socket resources.
- **[Risk] Partial directory deletion on error** → **Mitigation**: Use `shutil.rmtree` on `extracted_dir` only if it was newly created during the failed download attempt.

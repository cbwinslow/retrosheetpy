# Tasks

## 1. Documentation and Error Message Consistency

- [x] 1.1 Fix CLI command in `CLAUDE.md` to use `--conn` / `-f` instead of `--file`, and add note on default `--source github` and core dependencies. Verify by reading `CLAUDE.md`.
- [x] 1.2 Update `dlt` import error messages in `src/retrosheetpy/sink/dlt_sink.py` and `src/retrosheetpy/api.py` to say `'pip install dlt'` instead of stale extra `'pip install retrosheetpy[dlt]'`. Verify with `uv run pytest tests/test_sink.py`.

## 2. Downloader HTTP Session Reuse and Error Resilience

- [x] 2.1 Add persistent `httpx.Client` session management with connection pooling, `close()`, and context manager support (`__enter__` / `__exit__`) to `Downloader`. Verify with unit test in `tests/test_downloader_github.py`.
- [x] 2.2 Refactor `_get_events_github` in `src/retrosheetpy/extract/downloader.py` to handle HTTP 404s cleanly while raising network transport and timeout exceptions, preventing partial/corrupt season caches. Verify by writing unit tests covering network error fallback and 404 tolerance.
- [x] 2.3 Ensure cleanup of partial season directories if a network failure aborts season download before completion. Verify with tests in `tests/test_downloader_github.py`.

## 3. Verification & Decisions

- [x] 3.1 Run full test suite, lint, and type checking (`uv run pytest`, `uvx ruff check .`, `uv run mypy src`). Verify all checks pass with zero errors.
- [x] 3.2 Record architectural decisions and rationale in `docs/DECISIONS.md`. Verify by reading `docs/DECISIONS.md`.

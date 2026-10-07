# retrosheetpy — agent contract

Read `openspec/project.md` first. Contribution rules: `CONTRIBUTING.md`.

- Work through OpenSpec changes; use `superpowers:test-driven-development`.
- Do not reimplement Chadwick; call `chadwickpy`.
- No live-site calls in tests; no Retrosheet data committed.
- Record decisions in `docs/DECISIONS.md`.
- Verification: `uv run pytest`, `uvx ruff check .`, `uvx ruff format --check .`, `uvx mypy --strict src`.

# Contributing

Thanks for helping. Every change goes through a pull request that the maintainer approves.

1. Fork, branch, `uv sync`, then `uv run pytest`, `uvx ruff check .`, `uvx ruff format --check .`,
   `uvx mypy --strict src`.
2. Tests must not touch the live Retrosheet site: use a fake `fetch` and tiny captured fixtures.
3. Never commit Retrosheet data files.
4. Use [Conventional Commits](https://www.conventionalcommits.org/) in the PR title
   (`fix:`, `feat:`, `docs:`, `perf:`, `chore:`): versions and the changelog are generated from them.
5. Runtime dependencies stay minimal (today: `chadwickpy` only).
6. By contributing you agree your work is licensed GPL-3.0-or-later.

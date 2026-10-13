# retrosheetpy — Agent Contract

Read `openspec/project.md` first.

- **Architecture Rules:**
  - Keep Extract (`extract/`), Parse (`parse/`, `schemas/`), and Sink (`sink/`) decoupled through strict Python Protocols (`typing.Protocol`).
  - **Typing Mandate:** Every dataset MUST have an explicit, strongly-typed schema (PyArrow schema with `date32()`, `int32()`, `int16()`, `bool_()`, `float64()`, `string()`). No generic all-VARCHAR tables.
  - Integration with `chadwickpy`: Rely on `chadwickpy>=0.4.0` for parsing `.EVA`/`.EVN` event files and tool outputs (`cwevent`, `cwgame`, `cwdaily`, etc.).
- **Workflow:**
  - Work through OpenSpec changes (`openspec/changes/`).
  - Record decisions and schema rationale in `docs/DECISIONS.md`.
- **Testing & Verification:**
  - Unit tests with mock downloads and small fixtures run locally: `uv run pytest`.
  - Type-checking and linting: `uvx ruff check .`, `uvx ruff format --check .`, `uvx mypy --strict src`.
  - Heavy integration tests (large season downloads, multi-decade DuckDB loads) can be executed remotely on `cbwsff1`.

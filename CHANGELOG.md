# Changelog

## [2.0.0](https://github.com/cbwinslow/retrosheetpy/compare/v1.1.0...v2.0.0) (2026-10-13)


### ⚠ BREAKING CHANGES

* Complete architectural overhaul with decoupled extract/parse/schemas/sink modules, PyArrow strongly-typed schemas (164-col events, 161-col gamelogs, rosters, parks), DuckDB/Parquet/dlt/SQL sinks, and new CLI.

### Features

* overhaul architecture with strongly-typed multi-dataset pipeline (DuckDB, Parquet, dlt, SQL DDL) ([#19](https://github.com/cbwinslow/retrosheetpy/issues/19)) ([5f28b91](https://github.com/cbwinslow/retrosheetpy/commit/5f28b9178d9b7c4549805d4c1bc97a50557a471b))

## [1.1.0](https://github.com/cbwinslow/retrosheetpy/compare/v1.0.1...v1.1.0) (2026-10-09)


### Features

* tables, options, several seasons, output formats, new CLI (stacked on [#5](https://github.com/cbwinslow/retrosheetpy/issues/5)) ([#6](https://github.com/cbwinslow/retrosheetpy/issues/6)) ([295e3bc](https://github.com/cbwinslow/retrosheetpy/commit/295e3bc0d96bef4d91c0dda885ad5cc562c91a82))

## [1.0.1](https://github.com/cbwinslow/retrosheetpy/compare/v1.0.0...v1.0.1) (2026-10-07)


### Bug Fixes

* zip size and member caps, https-only fetch, stricter lint rules ([#5](https://github.com/cbwinslow/retrosheetpy/issues/5)) ([eafa30f](https://github.com/cbwinslow/retrosheetpy/commit/eafa30f761f6f568200882925c6cbed3372d6a0f))

## 1.0.0 (2026-10-05)


### Features

* download client, URL catalog and safe zip reading ([#1](https://github.com/cbwinslow/retrosheetpy/issues/1)) ([457ec52](https://github.com/cbwinslow/retrosheetpy/commit/457ec522fd692b4ea6681ec32dffb00320cf3925))

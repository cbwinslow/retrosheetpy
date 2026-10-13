# Change: Initial Architecture & Ingestion Pipeline

## Summary
Establish the foundational architecture for `retrosheetpy`:
1. Decoupled pipeline stages (`extract`, `schemas`, `parse`, `sink`).
2. Robust HTTP downloader with caching for Retrosheet zip archives (`events`, `gamelogs`, `rosters`, `biofile`, `parks`, `transactions`).
3. Strongly-typed schema definitions (PyArrow / DuckDB types: Date, Int, Bool, Float, String) for all major Retrosheet tables to prevent raw text ingestion.
4. Chadwick bridge integrating `chadwickpy` for event files.
5. Ingestion sinks for DuckDB, Parquet, and in-memory DataFrames (Polars, pandas, Arrow).
6. High-level user API (`import retrosheetpy as rs`) and CLI (`retrosheetpy`).

## Motivation
Researchers and sabermetricians need an automated, fast, pure-Python library to pull Retrosheet data directly into modern SQL engines (DuckDB) and dataframes without manually compiling C tools, writing brittle web scrapers, or writing custom type coercion scripts.

## Non-Goals
- Re-implementing the core Retrosheet play-by-play state machine (delegated to `chadwickpy`).
- Managing remote production database clusters (delegated to DuckDB/dlt).

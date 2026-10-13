# Capability: Retrosheet Ingestion

## ADDED Requirements

### Requirement: Database DDL Generation
The system MUST provide explicit SQL DDL generation for all Retrosheet datasets targeting PostgreSQL, DuckDB, and SQLite dialects so that DBAs can pre-create strongly-typed tables.

#### Scenario: Generating PostgreSQL DDL for events
- **WHEN** the user calls `rs.get_ddl("events", dialect="postgres")`
- **THEN** a valid `CREATE TABLE events (...)` SQL DDL string is returned containing correct PostgreSQL types (`DATE`, `SMALLINT`, `BOOLEAN`, `VARCHAR`).

### Requirement: Ingestion into Pre-Existing Database Tables
The system MUST support inserting parsed data into existing database tables without failing or dropping columns, aligning data by column name and using typed parameters.

#### Scenario: Inserting into pre-existing DuckDB table with custom schema
- **GIVEN** a DuckDB database with a pre-existing table `events`
- **WHEN** `rs.to_duckdb(path, years=[2024], mode="append")` is executed
- **THEN** data is appended matching column names without dropping or modifying the existing schema.

### Requirement: Cloud Warehouse Ingestion via dlt
The system MUST provide first-class `dlt` pipeline execution (`rs.to_dlt`) enabling direct automated loading into PostgreSQL, Snowflake, or BigQuery destinations.

#### Scenario: Running a dlt pipeline into PostgreSQL
- **GIVEN** a destination name or connection URL and selected years
- **WHEN** `rs.to_dlt(destination="duckdb", years=[2024], datasets=["parks"])` is called
- **THEN** a dlt pipeline executes and loads the data into the destination with verified schema contracts.

# SQL DDL Generator

When loading Retrosheet data into relational databases like **PostgreSQL**, **DuckDB**, or **SQLite**, having strongly-typed table definitions with primary keys, dates, and appropriate integer sizes is essential.

`retrosheetpy` includes a multi-dialect SQL DDL generator via `rs.get_ddl()`.

---

## Usage

Generate standard DDL statements by specifying the dataset name and the target dialect:

```python
import retrosheetpy as rs

# Generate PostgreSQL CREATE TABLE statement for game logs
print(rs.get_ddl("gamelogs", dialect="postgres"))

# Generate DuckDB CREATE TABLE statement for events
print(rs.get_ddl("events", dialect="duckdb"))

# Generate SQLite CREATE TABLE statement for rosters
print(rs.get_ddl("rosters", dialect="sqlite"))
```

---

## Supported Dialects & Type Mapping

| PyArrow Type | PostgreSQL Dialect | DuckDB Dialect | SQLite Dialect |
| :--- | :--- | :--- | :--- |
| `date32()` | `DATE` | `DATE` | `DATE` |
| `int16()` | `SMALLINT` | `SMALLINT` | `INTEGER` |
| `int32()` | `INTEGER` | `INTEGER` | `INTEGER` |
| `int64()` | `BIGINT` | `BIGINT` | `INTEGER` |
| `float64()` | `DOUBLE PRECISION` | `DOUBLE` | `REAL` |
| `bool_()` | `BOOLEAN` | `BOOLEAN` | `BOOLEAN` |
| `string()` | `VARCHAR` | `VARCHAR` | `TEXT` |

---

## Example: Generated PostgreSQL DDL (Game Logs)

```sql
CREATE TABLE IF NOT EXISTS game_logs (
    date DATE,
    game_number SMALLINT,
    day_of_week VARCHAR,
    visiting_team VARCHAR,
    visiting_league VARCHAR,
    visiting_game_num SMALLINT,
    home_team VARCHAR,
    home_league VARCHAR,
    home_game_num SMALLINT,
    visiting_score SMALLINT,
    home_score SMALLINT,
    outs_total SMALLINT,
    day_night VARCHAR,
    completion_info VARCHAR,
    forfeit_info VARCHAR,
    protest_info VARCHAR,
    park_id VARCHAR,
    attendance INTEGER,
    game_time_minutes SMALLINT,
    visiting_linescore VARCHAR,
    home_linescore VARCHAR,
    v_at_bats SMALLINT,
    v_hits SMALLINT,
    v_doubles SMALLINT,
    ...
    additional_info VARCHAR,
    acquisition_info VARCHAR
);
```

---

## CLI DDL Command

You can also print DDL directly in your terminal to pipe into database migration scripts or `psql`:

```bash
# Print Postgres DDL for play-by-play events
retrosheetpy ddl --dataset events --dialect postgres

# Pipe directly into a running Postgres database
retrosheetpy ddl --dataset gamelogs --dialect postgres | psql -U postgres -d retrosheet
```

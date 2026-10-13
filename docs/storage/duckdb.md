# DuckDB Integration

[DuckDB](https://duckdb.org) is the recommended analytical database engine for `retrosheetpy`. It runs in-process with zero server setup, processes millions of rows in milliseconds using vectorized execution, and queries Parquet and PyArrow memory directly.

---

## Direct Ingestion (`to_duckdb`)

The `to_duckdb` function downloads, extracts, and streams datasets into a DuckDB database file:

```python
import retrosheetpy as rs

# Ingest multiple seasons into a local database
rs.to_duckdb(
    path="baseball.duckdb",
    years=range(2020, 2025),
    datasets=["events", "gamelogs", "rosters", "parks"],
)
```

### Table Names Generated

| Dataset | DuckDB Table Name |
| :--- | :--- |
| `events` | `events` |
| `gamelogs` | `game_logs` |
| `rosters` | `rosters` |
| `parks` | `parks` |

---

## Querying DuckDB with SQL

Once ingested, you can query your data using standard SQL in Python, the DuckDB CLI, or DBeaver:

```python
import duckdb

con = duckdb.connect("baseball.duckdb")

# Top 5 most frequent matchups
matchups = con.execute("""
    SELECT
        visiting_team,
        home_team,
        COUNT(*) AS games_played,
        ROUND(AVG(visiting_score + home_score), 2) AS avg_runs
    FROM game_logs
    GROUP BY visiting_team, home_team
    ORDER BY games_played DESC
    LIMIT 5
""").fetchdf()

print(matchups)
```

---

## Column Alignment on Pre-Existing Tables

If you have an established database where tables were created in advance (or contain extra columns like `ingested_at` or `source`), `retrosheetpy` automatically:

1. Inspects the destination table's column names.
2. Identifies matching columns with the incoming Retrosheet data.
3. Performs column-aligned insertion:
   ```sql
   INSERT INTO game_logs (date, visiting_team, visiting_score, ...)
   SELECT date, visiting_team, visiting_score, ...
   FROM _incoming_arrow;
   ```
4. Leaves any unmapped columns set to their default or null values.

```python
import duckdb
import retrosheetpy as rs

con = duckdb.connect("existing.duckdb")

# Pre-create table with custom subset of columns
con.execute("""
    CREATE TABLE IF NOT EXISTS game_logs (
        date DATE,
        visiting_team VARCHAR,
        visiting_score SMALLINT,
        home_team VARCHAR,
        home_score SMALLINT
    )
""")

# Ingest - only matching columns are inserted!
rs.to_duckdb("existing.duckdb", years=[2024], datasets=["gamelogs"])
```

# Postseason & All-Star Games

In addition to regular season play-by-play archives, Retrosheet distributes dedicated event files for **Postseason** series (World Series, LCS, LDS, Wild Card) and the annual **All-Star Game**.

`retrosheetpy` parses these specialty archives directly through the standard 164-column Chadwick event schema contract.

---

## Python API Usage

```python
import retrosheetpy as rs

# 1. Fetch 2024 Postseason events into Polars
post_df = rs.postseason(2024, backend="polars")
print(f"Total Postseason plays: {len(post_df)}")

# 2. Fetch 2024 All-Star Game events into Polars
as_df = rs.allstar(2024, backend="polars")

# 3. Export Postseason events to Parquet
rs.to_parquet("postseason_2024.parquet", dataset="postseason", years=2024)

# 4. Ingest Postseason & All-Star into DuckDB
rs.to_duckdb(
    "october.duckdb",
    years=[2021, 2022, 2023, 2024],
    datasets=["postseason", "allstar"],
)
```

---

## CLI Usage

```bash
# Download and cache Postseason & All-Star archives
retrosheetpy download -s postseason,allstar -y 2024

# Export 2024 Postseason to Parquet
retrosheetpy export -s postseason -y 2024 -f parquet -o postseason_2024.parquet

# Export 2024 All-Star Game to CSV
retrosheetpy export -s allstar -y 2024 -f csv -o allstar_2024.csv

# Ingest into local DuckDB
retrosheetpy ingest -d duckdb -c fall_classic.duckdb -s postseason -y 2020-2024
```

---

## Schema Contract

Both `postseason` and `allstar` events conform directly to `EVENT_SCHEMA` (164 fields), providing pitch sequences, hit coordinates, base runner advances, pickoff attempts, and run expectancy states identical to regular season events.

For complete field definitions and physical data types, see the [Play-by-Play Events Reference](events.md).

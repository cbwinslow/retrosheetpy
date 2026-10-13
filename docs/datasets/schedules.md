# Official Schedules

Retrosheet publishes regular season schedule files for every season in Major League Baseball history (1877–present).

Each season's archive (`YYYYSKED.zip`) contains the game date, doubleheader number, opponent matchups, leagues, day/night flag, venue, postponed status, and makeup date.

---

## Python API Usage

```python
import retrosheetpy as rs

# 1. Fetch 2024 schedule into Polars
sked_df = rs.schedules(2024, backend="polars")
print(sked_df.select(["date", "vis_team", "home_team", "day_night", "postponed"]))

# 2. Fetch multi-year schedules into PyArrow Table
sked_tbl = rs.schedules(range(2020, 2025), backend="arrow")

# 3. Export to Parquet
rs.to_parquet("schedules_2024.parquet", dataset="schedules", years=2024)
```

---

## CLI Usage

```bash
# Download and cache schedule files
retrosheetpy download -s schedules -y 2024

# Export to Parquet
retrosheetpy export -s schedules -y 2024 -f parquet -o schedules_2024.parquet

# Generate BigQuery SQL DDL
retrosheetpy ddl -s schedules --dialect bigquery

# Ingest into DuckDB
retrosheetpy ingest -d duckdb -c baseball.duckdb -s schedules -y 2024
```

---

## PyArrow Schema (`SCHEDULE_SCHEMA`)

| Column Name | Arrow Type | SQL (Postgres / BigQuery) | Description |
| :--- | :--- | :--- | :--- |
| `date` | `pa.date32()` | `DATE` | Scheduled game date (`YYYY-MM-DD`). |
| `game_num` | `pa.int8()` | `SMALLINT` / `INT64` | `0` for single game, `1`/`2` for doubleheaders. |
| `day_of_week` | `pa.string()` | `VARCHAR` / `STRING` | Three-letter or full day of week (`Mon`, `Tue`, etc.). |
| `vis_team` | `pa.string()` | `VARCHAR` / `STRING` | Visiting team three-letter abbreviation (e.g. `LAN`). |
| `vis_league` | `pa.string()` | `VARCHAR` / `STRING` | Visiting team league (`AL`, `NL`, `AA`, etc.). |
| `vis_game_num` | `pa.int16()` | `SMALLINT` / `INT64` | Visiting team's game number in season. |
| `home_team` | `pa.string()` | `VARCHAR` / `STRING` | Home team three-letter abbreviation (e.g. `SDN`). |
| `home_league` | `pa.string()` | `VARCHAR` / `STRING` | Home team league (`AL`, `NL`, etc.). |
| `home_game_num` | `pa.int16()` | `SMALLINT` / `INT64` | Home team's game number in season. |
| `day_night` | `pa.string()` | `VARCHAR` / `STRING` | `D` for Day game, `N` for Night game. |
| `park_id` | `pa.string()` | `VARCHAR` / `STRING` | Neutral site or special ballpark ID if applicable. |
| `postponed` | `pa.string()` | `VARCHAR` / `STRING` | Postponement reason (e.g. `Rain`, `Cold`, `Strike`) or empty. |
| `makeup_date` | `pa.date32()` | `DATE` | Rescheduled makeup date if postponed. |

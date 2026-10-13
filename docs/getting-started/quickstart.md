# 5-Minute Quickstart

This guide walks through downloading Retrosheet data, querying play-by-play events, and saving datasets to DuckDB and Parquet.

---

## 1. Downloading & Inspecting Events

To fetch every play of the 2024 MLB season (all ~188,000 plays across 2,429 games):

```python
import retrosheetpy as rs

# Download, cache, and parse 2024 play-by-play
events = rs.events(year=2024, backend="polars")

# Inspect plays
print(events.select(["GAME_ID", "INN_CT", "BAT_ID", "PIT_ID", "EVENT_TX"]).head(10))
```

The returned table contains **164 strongly-typed columns**, including count, pitch sequence, base runners, event codes, and defensive alignment.

---

## 2. Historical Game Logs (1871–Present)

Retrosheet provides game-by-game summary logs with line scores, starting lineups, umpire crews, and attendance.

```python
import retrosheetpy as rs

# Fetch multiple seasons at once
gl = rs.game_logs(year=[2023, 2024], backend="polars")

# Find the highest scoring games of 2024
high_scoring = gl.filter(gl["visiting_score"] + gl["home_score"] > 20).select(
    ["date", "visiting_team", "visiting_score", "home_team", "home_score"]
)
print(high_scoring)
```

---

## 3. Ballparks & Rosters

Explore the historical ballpark encyclopedia and official team rosters:

```python
import retrosheetpy as rs

# 1. Complete ballpark directory (260 historical major league parks)
parks = rs.parks(backend="polars")
print(parks.filter(parks["city"] == "Chicago"))

# 2. 2024 Player rosters
rosters = rs.rosters(year=2024, backend="polars")
shohei = rosters.filter(rosters["last_name"] == "Ohtani")
print(shohei)
```

---

## 4. Ingesting into DuckDB

Instead of storing gigabytes of raw CSV or text files, you can stream multiple seasons and datasets directly into an embedded **DuckDB** file:

```python
import retrosheetpy as rs

# Ingest full 2020-2024 seasons into local DuckDB
rs.to_duckdb(
    path="retro.duckdb",
    years=range(2020, 2025),
    datasets=["events", "gamelogs", "rosters", "parks"],
)
```

Now connect to DuckDB directly with SQL:

```python
import duckdb

con = duckdb.connect("retro.duckdb")

# Top home run hitters of 2024
top_hr = con.execute("""
    SELECT BAT_ID, COUNT(*) AS home_runs
    FROM events
    WHERE HR_FL = TRUE AND YEAR = 2024
    GROUP BY BAT_ID
    ORDER BY home_runs DESC
    LIMIT 10
""").fetchdf()

print(top_hr)
```

---

## 5. Exporting to Parquet

For fast columnar storage in S3 or local data lakes:

```python
import retrosheetpy as rs

rs.to_parquet(
    path="gamelogs_2000_2024.parquet",
    dataset="gamelogs",
    years=range(2000, 2025),
)
```

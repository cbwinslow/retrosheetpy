# Recipe: Ballpark Factors & Scoring Environments

A **Park Factor (PF)** measures how much a specific ballpark inflates or deflates run scoring compared to an average stadium.

A park factor of `100` is neutral. Values above `100` (e.g. `115` at Coors Field) indicate hitter-friendly parks, while values below `100` (e.g. `88` at Petco Park) indicate pitcher-friendly environments.

---

## The Formula

The standard basic 1-year Run Park Factor is:

$$\text{PF} = \frac{\frac{\text{Runs at Home}}{\text{Games at Home}}}{\frac{\text{Runs on Road}}{\text{Games on Road}}} \times 100$$

---

## Calculating Park Factors with DuckDB

```python
import retrosheetpy as rs
import duckdb

# Ingest 2024 game logs and parks into DuckDB
rs.to_duckdb("retro.duckdb", years=[2024], datasets=["gamelogs", "parks"])

con = duckdb.connect("retro.duckdb")

query = """
WITH home_runs_scored AS (
    SELECT 
        home_team AS team,
        park_id,
        COUNT(*) AS home_games,
        SUM(home_score + visiting_score) AS home_runs
    FROM game_logs
    GROUP BY home_team, park_id
),
road_runs_scored AS (
    SELECT 
        visiting_team AS team,
        COUNT(*) AS road_games,
        SUM(home_score + visiting_score) AS road_runs
    FROM game_logs
    GROUP BY visiting_team
)
SELECT 
    p.name AS ballpark,
    h.team,
    h.home_games,
    h.home_runs,
    r.road_runs,
    ROUND(((h.home_runs / h.home_games) / (r.road_runs / r.road_games)) * 100, 1) AS park_factor
FROM home_runs_scored h
JOIN road_runs_scored r ON h.team = r.team
JOIN parks p ON h.park_id = p.park_id
ORDER BY park_factor DESC;
"""

pf_df = con.execute(query).fetchdf()
print(pf_df.head(10))
```

---

## Multi-Year Park Factors

Because a single 81-game home schedule has natural noise, sabermetricians typically average 3 to 5 seasons of game logs:

```python
# Ingest 2020 through 2024
rs.to_duckdb("retro.duckdb", years=range(2020, 2025), datasets=["gamelogs", "parks"])
```
Running the same SQL query across the 5-year table yields stabilized 5-year park factors.

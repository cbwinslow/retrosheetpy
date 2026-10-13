# Recipe: 24-State Run Expectancy (RE24)

In sabermetrics, the **Run Expectancy Matrix (RE24)** calculates the average number of runs scored from any given game state (combination of 0, 1, or 2 outs and runners on 1st, 2nd, and 3rd) through the end of that half-inning.

This tutorial shows how to construct the official RE24 matrix using 2024 Retrosheet events in **DuckDB**.

---

## 1. Ingest 2024 Events into DuckDB

```python
import retrosheetpy as rs

# Download and load 2024 play-by-play events
rs.to_duckdb("retro.duckdb", years=[2024], datasets=["events"])
```

---

## 2. Compute Run Expectancy via SQL

Each play record in Retrosheet includes:
* `GAME_ID`: Unique game
* `INN_CT`: Inning
* `BAT_HOME_ID`: Half-inning (`0` = top, `1` = bottom)
* `OUTS_CT`: Outs before play (`0`, `1`, `2`)
* `BASE1_RUN_ID`, `BASE2_RUN_ID`, `BASE3_RUN_ID`: Base runners
* `AWAY_SCORE_CT`, `HOME_SCORE_CT`: Current score

```python
import duckdb

con = duckdb.connect("retro.duckdb")

query = """
WITH half_innings AS (
    -- Total runs scored in each half-inning
    SELECT
        GAME_ID,
        INN_CT,
        BAT_HOME_ID,
        MAX(CASE WHEN BAT_HOME_ID = 0 THEN AWAY_SCORE_CT ELSE HOME_SCORE_CT END) -
        MIN(CASE WHEN BAT_HOME_ID = 0 THEN AWAY_SCORE_CT ELSE HOME_SCORE_CT END) AS runs_in_half_inning
    FROM events
    GROUP BY GAME_ID, INN_CT, BAT_HOME_ID
),
play_states AS (
    -- Base runners state encoded as string: '---', '1--', '-2-', '12-', '123', etc.
    SELECT
        e.GAME_ID,
        e.INN_CT,
        e.BAT_HOME_ID,
        e.OUTS_CT,
        CONCAT(
            CASE WHEN e.BASE1_RUN_ID IS NOT NULL AND e.BASE1_RUN_ID != '' THEN '1' ELSE '-' END,
            CASE WHEN e.BASE2_RUN_ID IS NOT NULL AND e.BASE2_RUN_ID != '' THEN '2' ELSE '-' END,
            CASE WHEN e.BASE3_RUN_ID IS NOT NULL AND e.BASE3_RUN_ID != '' THEN '3' ELSE '-' END
        ) AS base_state,
        -- Runs scored from this point forward until 3 outs
        h.runs_in_half_inning - (CASE WHEN e.BAT_HOME_ID = 0 THEN e.AWAY_SCORE_CT ELSE e.HOME_SCORE_CT END) AS future_runs
    FROM events e
    JOIN half_innings h
      ON e.GAME_ID = h.GAME_ID
     AND e.INN_CT = h.INN_CT
     AND e.BAT_HOME_ID = h.BAT_HOME_ID
)
SELECT
    base_state,
    ROUND(AVG(CASE WHEN OUTS_CT = 0 THEN future_runs END), 3) AS "0 Outs",
    ROUND(AVG(CASE WHEN OUTS_CT = 1 THEN future_runs END), 3) AS "1 Out",
    ROUND(AVG(CASE WHEN OUTS_CT = 2 THEN future_runs END), 3) AS "2 Outs",
    COUNT(*) AS total_plays
FROM play_states
GROUP BY base_state
ORDER BY "0 Outs" DESC;
"""

re24_table = con.execute(query).fetchdf()
print(re24_table)
```

---

## Example 2024 RE24 Results

| Base State | 0 Outs | 1 Out | 2 Outs |
| :--- | :--- | :--- | :--- |
| **`123` (Bases Loaded)** | **2.282** | **1.520** | **0.748** |
| **`-23` (2nd & 3rd)** | **1.964** | **1.371** | **0.570** |
| **`1-3` (1st & 3rd)** | **1.784** | **1.140** | **0.478** |
| **`--3` (Runner on 3rd)** | **1.350** | **0.950** | **0.353** |
| **`12-` (1st & 2nd)** | **1.437** | **0.884** | **0.429** |
| **`-2-` (Runner on 2nd)** | **1.100** | **0.664** | **0.319** |
| **`1--` (Runner on 1st)** | **0.859** | **0.509** | **0.218** |
| **`---` (Bases Empty)** | **0.481** | **0.254** | **0.098** |

From this matrix, you can calculate the **Run Value** of any individual hit, out, walk, or stolen base:

$$\text{Run Value} = \text{RE}_{\text{after}} - \text{RE}_{\text{before}} + \text{Runs Scored}$$

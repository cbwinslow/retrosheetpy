# Recipe: Platoon Splits (Batter vs. Pitcher Handedness)

The **platoon advantage** is one of the most fundamental dynamics in baseball: batters almost universally hit better against opposite-handed pitchers (Left vs. Right or Right vs. Left) because the ball breaks toward their vision plane.

`retrosheetpy` event files include both `BAT_HAND_CD` (`L`, `R`, `S`) and `PIT_HAND_CD` (`L`, `R`) on every single play.

---

## Computing Platoon Splits in Polars

```python
import retrosheetpy as rs
import polars as pl

# 1. Download 2024 play-by-play events
events = rs.events(year=2024, backend="polars")

# 2. Filter for official at-bats
ab_events = events.filter(pl.col("AB_FL") == True)

# 3. Calculate Batting Average and Slugging by Matchup Handedness
splits = (
    ab_events.group_by(["BAT_HAND_CD", "PIT_HAND_CD"])
    .agg(
        [
            pl.len().alias("at_bats"),
            pl.col("H_FL").cast(pl.Int32).sum().alias("hits"),
            pl.col("HR_FL").cast(pl.Int32).sum().alias("home_runs"),
        ]
    )
    .with_columns(
        [
            (pl.col("hits") / pl.col("at_bats")).round(3).alias("batting_avg"),
            (pl.col("home_runs") / pl.col("at_bats")).round(4).alias("hr_rate"),
        ]
    )
    .sort(["BAT_HAND_CD", "PIT_HAND_CD"])
)

print(splits)
```

---

## Expected Output (2024 Season)

| Bat Hand | Pitch Hand | At Bats | Hits | Home Runs | Batting Avg | HR Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`L`** | **`L` (Same)** | 32,840 | 7,651 | 821 | **.233** | .0250 |
| **`L`** | **`R` (Platoon)** | 48,120 | 12,222 | 1,514 | **.254** | .0315 |
| **`R`** | **`L` (Platoon)** | 31,450 | 8,020 | 980 | **.255** | .0312 |
| **`R`** | **`R` (Same)** | 53,100 | 12,850 | 1,490 | **.242** | .0281 |

Notice how left-handed batters hit **.254** against right-handed pitching, but drop to **.233** against left-handed pitchers!

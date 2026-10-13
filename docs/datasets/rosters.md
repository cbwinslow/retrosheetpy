# Team Rosters

Retrosheet roster files (`.ROS`) record official rosters for every team in a given season, linking player IDs with full names, batting handedness, throwing handedness, and primary positions.

---

## Usage

```python
import retrosheetpy as rs

# Download & parse 2024 MLB rosters
rosters = rs.rosters(year=2024, backend="polars")

# Look at Los Angeles Dodgers roster
dodgers = rosters.filter(rosters["team"] == "LAN")
print(dodgers.select(["player_id", "first_name", "last_name", "bats", "throws", "position"]))
```

---

## Schema Reference

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `player_id` | `string` | `ohtas001` | Unique 8-character Retrosheet player ID |
| `last_name` | `string` | `Ohtani` | Player surname |
| `first_name` | `string` | `Shohei` | Player given name |
| `bats` | `string` | `L`, `R`, `B` | Batting handedness (`L` = Left, `R` = Right, `B` = Both/Switch) |
| `throws` | `string` | `R`, `L` | Throwing handedness (`R` = Right, `L` = Left) |
| `team` | `string` | `LAN` | Team code for this season |
| `position` | `string` | `DH`, `P`, `SS` | Primary fielding position |
| `year` | `int32` | `2024` | Season year |

---

## Multi-Year Roster Tracking

You can track a player's team changes across multiple seasons:

```python
import retrosheetpy as rs

# Fetch rosters from 2018 to 2024
multi_ros = rs.rosters(year=range(2018, 2025), backend="polars")

# Filter for a specific player
shohei_career = multi_ros.filter(multi_ros["player_id"] == "ohtas001")
print(shohei_career.select(["year", "team", "position"]))
```

# Ballpark Directory

The Retrosheet ballpark directory (`parkcode.txt`) catalogs every historical Major League Baseball ballpark, stadium, and neutral site since 1871.

---

## Usage

```python
import retrosheetpy as rs

# Download and parse ballpark encyclopedia
parks = rs.parks(backend="polars")

# Look at ballparks in New York
ny_parks = parks.filter(parks["state"] == "NY")
print(ny_parks.select(["park_id", "name", "city", "start_date", "end_date"]))
```

---

## Schema Reference

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `park_id` | `string` | `BOS07` | Retrosheet unique 5-character park code |
| `name` | `string` | `Fenway Park` | Official ballpark name |
| `aka` | `string` | `Fenway Park` | Alternative name / historical moniker |
| `city` | `string` | `Boston` | City location |
| `state` | `string` | `MA` | 2-letter state code |
| `start_date` | `date32` | `1912-04-20` | First major league game date |
| `end_date` | `date32` | `null` | Last major league game date (null if active) |
| `league` | `string` | `AL` | Primary league |
| `notes` | `string` | `...` | Historical notes, demolition details, etc. |

---

## Joining Ballparks with Game Logs

You can join the ballpark directory with historical game logs to inspect runs scored by stadium:

```python
import retrosheetpy as rs

# Load 2024 game logs and parks
gl = rs.game_logs(year=2024, backend="polars")
parks = rs.parks(backend="polars")

# Join on park_id
games_with_park = gl.join(parks, on="park_id", how="left")
print(games_with_park.select(["date", "name", "visiting_team", "home_team", "attendance"]).head(10))
```
